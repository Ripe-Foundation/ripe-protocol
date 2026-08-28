import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


def _execute(switchboard, governance, action_id):
    boa.env.time_travel(blocks=max(switchboard.actionTimeLock(), 1))
    return switchboard.executePendingAction(action_id, sender=governance.address)


def _set_deposit_params(
    switchboard_bravo,
    governance,
    asset,
    vault_ids,
    stakers,
    voters,
    mission_control=ZERO_ADDRESS,
):
    return switchboard_bravo.setAssetDepositParams(
        asset,
        vault_ids,
        stakers,
        voters,
        2_000 * EIGHTEEN_DECIMALS,
        20_000 * EIGHTEEN_DECIMALS,
        0,
        mission_control,
        sender=governance.address,
    )


def _set_stored_points_flag(mission_control, switchboard_alpha, enabled):
    config = list(mission_control.rewardsConfig())
    config[0] = enabled
    mission_control.setRipeRewardsConfig(
        config,
        sender=switchboard_alpha.address,
    )


def test_update_deposit_points_works_while_lootbox_paused_but_claim_reverts(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    alpha_token,
    alpha_token_whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
    ledger,
    teller,
    switchboard_alpha,
    bob,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        25 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)

    lootbox.pause(True, sender=switchboard_alpha.address)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate != 0
    with boa.reverts("contract paused"):
        lootbox.claimDepositLootForAsset(
            bob,
            vault_id,
            alpha_token,
            sender=teller.address,
        )


def test_reset_paths_revert_on_empty_book_user_or_asset(
    lootbox,
    switchboard_delta,
    alpha_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with boa.reverts("invalid reset"):
        lootbox.resetUserBalancePoints(
            ZERO_ADDRESS,
            alpha_token,
            vault_id,
            sender=switchboard_delta.address,
        )
    with boa.reverts("invalid reset"):
        lootbox.resetAssetPoints(
            ZERO_ADDRESS,
            vault_id,
            sender=switchboard_delta.address,
        )
    with boa.reverts("invalid reset"):
        lootbox.resetAssetPoints(
            alpha_token,
            MAX_UINT256,
            sender=switchboard_delta.address,
        )
    with boa.reverts("invalid reset"):
        lootbox.resetUserBorrowPoints(
            ZERO_ADDRESS,
            sender=switchboard_delta.address,
        )


def test_two_vaults_only_earner_accrues_staker_points_and_global_counts_once(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    alpha_token,
    alpha_token_whale,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    lootbox,
    ledger,
    teller,
    switchboard_bravo,
    mission_control,
    bob,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    setGeneralConfig()
    setRipeRewardsConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        vault_a,
        sender=switchboard_bravo.address,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=10,
        _voterPointsAlloc=0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        25 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
    )
    performDeposit(
        bob,
        25 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        rebase_erc20_vault,
    )
    lootbox.updateDepositPoints(
        bob, vault_a, simple_erc20_vault, alpha_token, sender=teller.address
    )
    lootbox.updateDepositPoints(
        bob, vault_b, rebase_erc20_vault, alpha_token, sender=teller.address
    )
    a_before = ledger.assetDepositPoints(vault_a, alpha_token)
    b_before = ledger.assetDepositPoints(vault_b, alpha_token)
    global_before = ledger.globalDepositPoints()

    elapsed = 7
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(
        bob, vault_b, rebase_erc20_vault, alpha_token, sender=teller.address
    )
    lootbox.updateDepositPoints(
        bob, vault_a, simple_erc20_vault, alpha_token, sender=teller.address
    )

    a_after = ledger.assetDepositPoints(vault_a, alpha_token)
    b_after = ledger.assetDepositPoints(vault_b, alpha_token)
    global_after = ledger.globalDepositPoints()
    assert a_after.ripeStakerPoints == a_before.ripeStakerPoints + 10 * elapsed
    assert b_after.ripeStakerPoints == b_before.ripeStakerPoints
    assert global_after.ripeStakerPoints == global_before.ripeStakerPoints + 10 * elapsed
    assert mission_control.totalPointsAllocs().stakersPointsAllocTotal == 10


def test_should_fund_gen_points_only_for_earner_when_stakers_are_zero(
    setAssetConfig,
    alpha_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    switchboard_bravo,
    mission_control,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        vault_a,
        sender=switchboard_bravo.address,
    )

    earner = mission_control.getDepositPointsConfig(alpha_token, vault_a)
    non_earner = mission_control.getDepositPointsConfig(alpha_token, vault_b)
    assert earner.shouldFundGenPoints
    assert not non_earner.shouldFundGenPoints
    assert non_earner.stakersPointsAlloc == 0
    assert non_earner.voterPointsAlloc == 0


def test_bravo_refuses_nonzero_allocs_without_an_earner(
    setAssetConfig,
    alpha_token,
    simple_erc20_vault,
    vault_book,
    switchboard_bravo,
    mission_control,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    assert mission_control.rewardVaultId(alpha_token) == 0
    action_id = _set_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        5,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    with boa.reverts("active allocs require reward vault"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )


def test_bravo_refuses_dropping_the_live_earner(
    setAssetConfig,
    alpha_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    switchboard_bravo,
    mission_control,
    governance,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        vault_a,
        sender=switchboard_bravo.address,
    )
    action_id = _set_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_b],
        0,
        0,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    with boa.reverts("cannot drop reward vault"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )


def test_bravo_initiate_refuses_stakers_when_earner_is_not_core_or_stab(
    setAssetConfig,
    alpha_token,
    simple_erc20_vault,
    vault_book,
    switchboard_bravo,
    mission_control,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert vault_id != mission_control.coreRipeGovVaultId()
    assert not mission_control.isStabVaultId(vault_id)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        vault_id,
        sender=switchboard_bravo.address,
    )
    with boa.reverts("invalid asset deposit params"):
        _set_deposit_params(
            switchboard_bravo,
            governance,
            alpha_token,
            [vault_id],
            5,
            0,
        )


def test_charlie_rotation_fences_initialized_new_earner_history(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    alpha_token,
    alpha_token_whale,
    stability_pool,
    ripe_gov_vault,
    vault_book,
    lootbox,
    ledger,
    teller,
    switchboard_alpha,
    switchboard_charlie,
    mission_control,
    governance,
    bob,
):
    vault_a = vault_book.getRegId(stability_pool)
    vault_b = vault_book.getRegId(ripe_gov_vault)
    assert mission_control.isStabVaultId(vault_a)
    assert vault_b == mission_control.coreRipeGovVaultId()

    setGeneralConfig()
    setRipeRewardsConfig(
        _ripePerBlock=10,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    ledger.setRipeAvailForRewards(
        10**24,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=8,
        _voterPointsAlloc=0,
    )
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        100_00,
        False,
        (0, 1_000, 100_00, True, 0),
        sender=switchboard_alpha.address,
    )
    assert mission_control.rewardVaultId(alpha_token) == vault_a
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    amount = 25 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
        stability_pool,
    )
    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
        ripe_gov_vault,
    )
    lootbox.updateDepositPoints(
        bob,
        vault_a,
        stability_pool,
        alpha_token,
        sender=teller.address,
    )
    lootbox.updateDepositPoints(
        bob,
        vault_b,
        ripe_gov_vault,
        alpha_token,
        sender=teller.address,
    )
    a_before = ledger.assetDepositPoints(vault_a, alpha_token)
    b_before = ledger.assetDepositPoints(vault_b, alpha_token)
    global_before = ledger.globalDepositPoints()
    assert b_before.lastUpdate != 0

    rotate_id = switchboard_charlie.setRewardVaultId(
        alpha_token,
        vault_b,
        sender=governance.address,
    )
    assert _execute(switchboard_charlie, governance, rotate_id)

    a_after = ledger.assetDepositPoints(vault_a, alpha_token)
    b_after = ledger.assetDepositPoints(vault_b, alpha_token)
    global_after = ledger.globalDepositPoints()
    elapsed = a_after.lastUpdate - a_before.lastUpdate
    assert elapsed >= switchboard_charlie.actionTimeLock()
    assert a_after.ripeStakerPoints == a_before.ripeStakerPoints + 8 * elapsed
    assert b_after.ripeStakerPoints == b_before.ripeStakerPoints
    assert global_after.ripeStakerPoints == (
        global_before.ripeStakerPoints + 8 * elapsed
    )

    global_before_b_claim = ledger.globalDepositPoints().ripeStakerPoints
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_b, alpha_token) == 0
    assert (
        lootbox.claimDepositLootForAsset(
            bob,
            vault_b,
            alpha_token,
            sender=teller.address,
        )
        == 0
    )
    assert ledger.globalDepositPoints().ripeStakerPoints == global_before_b_claim
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_a, alpha_token) > 0
    assert (
        lootbox.claimDepositLootForAsset(
            bob,
            vault_a,
            alpha_token,
            sender=teller.address,
        )
        > 0
    )


def test_charlie_can_clear_live_earner_then_zero_allocs_without_starting_gen(
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    mock_price_source,
    alpha_token,
    alpha_token_whale,
    stability_pool,
    ripe_gov_vault,
    vault_book,
    lootbox,
    ledger,
    teller,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    mission_control,
    governance,
    bob,
):
    vault_a = vault_book.getRegId(stability_pool)
    vault_b = vault_book.getRegId(ripe_gov_vault)
    assert mission_control.isStabVaultId(vault_a)
    assert vault_b == mission_control.coreRipeGovVaultId()
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_a, vault_b],
        _stakersPointsAlloc=8,
        _voterPointsAlloc=0,
    )
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        100_00,
        False,
        (0, 1_000, 100_00, True, 0),
        sender=switchboard_alpha.address,
    )
    assert mission_control.rewardVaultId(alpha_token) == vault_a
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        25 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        ripe_gov_vault,
    )
    lootbox.updateDepositPoints(
        bob,
        vault_b,
        ripe_gov_vault,
        alpha_token,
        sender=teller.address,
    )
    b_before = ledger.assetDepositPoints(vault_b, alpha_token)
    assert b_before.lastUpdate != 0

    clear_id = switchboard_charlie.setRewardVaultId(
        alpha_token,
        0,
        sender=governance.address,
    )
    zero_id = _set_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_a, vault_b],
        0,
        0,
    )
    restore_id = _set_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_a, vault_b],
        8,
        0,
    )

    boa.env.time_travel(
        blocks=max(
            switchboard_charlie.actionTimeLock(),
            switchboard_bravo.actionTimeLock(),
            1,
        )
    )
    assert switchboard_charlie.executePendingAction(
        clear_id,
        sender=governance.address,
    )
    assert mission_control.rewardVaultId(alpha_token) == 0
    config_after_clear = mission_control.getDepositPointsConfig(alpha_token, vault_a)
    assert config_after_clear.stakersPointsAlloc == 0
    assert config_after_clear.voterPointsAlloc == 0
    assert not config_after_clear.shouldFundGenPoints

    assert switchboard_bravo.executePendingAction(
        zero_id,
        sender=governance.address,
    )
    config_after_zero = mission_control.getDepositPointsConfig(alpha_token, vault_a)
    assert config_after_zero.stakersPointsAlloc == 0
    assert config_after_zero.voterPointsAlloc == 0
    assert not config_after_zero.shouldFundGenPoints

    select_id = switchboard_charlie.setRewardVaultId(
        alpha_token,
        vault_b,
        sender=governance.address,
    )
    assert _execute(switchboard_charlie, governance, select_id)
    b_after_select = ledger.assetDepositPoints(vault_b, alpha_token)
    assert b_after_select.ripeStakerPoints == b_before.ripeStakerPoints
    assert b_after_select.ripeGenPoints == b_before.ripeGenPoints

    assert switchboard_bravo.executePendingAction(
        restore_id,
        sender=governance.address,
    )
    config_after_restore = mission_control.getDepositPointsConfig(alpha_token, vault_b)
    assert config_after_restore.stakersPointsAlloc == 8
    assert config_after_restore.voterPointsAlloc == 0
    assert not config_after_restore.shouldFundGenPoints
    b_after_restore = ledger.assetDepositPoints(vault_b, alpha_token)
    assert b_after_restore.lastUpdate > b_before.lastUpdate
    assert b_after_restore.ripeStakerPoints == b_before.ripeStakerPoints
    assert b_after_restore.ripeGenPoints == b_before.ripeGenPoints


def test_charlie_historical_checkpoint_reverts_on_empty_book_or_addr_mismatch(
    switchboard_charlie,
    governance,
    alpha_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with boa.reverts("vault addr mismatch"):
        switchboard_charlie.checkpointAssetDepositPointsAt(
            alpha_token,
            vault_id,
            rebase_erc20_vault,
            sender=governance.address,
        )

    assert vault_book.startAddressDisableInRegistry(
        vault_id,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressDisableInRegistry(
        vault_id,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == ZERO_ADDRESS
    with boa.reverts("vault addr mismatch"):
        switchboard_charlie.checkpointAssetDepositPointsAt(
            alpha_token,
            vault_id,
            simple_erc20_vault,
            sender=governance.address,
        )


def test_bravo_deposit_params_execute_reverts_when_pending_mc_is_not_current(
    setAssetConfig,
    alpha_token,
    simple_erc20_vault,
    vault_book,
    switchboard_bravo,
    mission_control,
    ripe_hq,
    defaults,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    action_id = _set_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        0,
    )
    assert switchboard_bravo.pendingMissionControl(action_id) == mission_control.address

    replacement = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="reward_clock_stale_pending_mc",
    )
    assert ripe_hq.startAddressUpdateToRegistry(
        5,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(5, sender=governance.address)
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))

    with boa.reverts("not current mission control"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )


def test_raw_reward_setters_revert_on_non_current_mission_control(
    alpha_token,
    mission_control,
    ripe_hq,
    defaults,
    switchboard_alpha,
    switchboard_bravo,
):
    candidate = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="reward_clock_non_current_mc",
    )
    assert candidate.address != mission_control.address
    with boa.reverts("not current mission control"):
        candidate.setRipeRewardsConfig(
            mission_control.rewardsConfig(),
            sender=switchboard_alpha.address,
        )
    with boa.reverts("not current mission control"):
        candidate.setRewardVaultId(
            alpha_token,
            1,
            sender=switchboard_bravo.address,
        )


def test_clocks_move_when_stored_are_points_enabled_is_false(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
    ledger,
    teller,
    credit_engine,
    switchboard_alpha,
    mission_control,
    bob,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(True, 5, 25_00, 25_00, 25_00, 25_00)
    _set_stored_points_flag(mission_control, switchboard_alpha, False)
    assert not mission_control.rewardsConfig().arePointsEnabled
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        25 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    debt_terms = createDebtTerms()
    ledger.setUserDebt(
        bob,
        (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False),
        0,
        (0, 0),
        sender=credit_engine.address,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(
        bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address
    )
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    deposit_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    borrow_before = ledger.userBorrowPoints(bob)
    rewards_before = ledger.ripeRewards().lastUpdate

    boa.env.time_travel(blocks=6)
    lootbox.updateDepositPoints(
        bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address
    )
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    assert (
        ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints
        > deposit_before.balancePoints
    )
    assert ledger.userBorrowPoints(bob).points > borrow_before.points
    assert ledger.ripeRewards().lastUpdate > rewards_before
