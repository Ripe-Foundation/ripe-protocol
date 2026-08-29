import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


def _execute(board, governance, action_id):
    boa.env.time_travel(blocks=board.actionTimeLock())
    assert board.executePendingAction(action_id, sender=governance.address)


def _add_promotional_asset(
    switchboard_golf,
    governance,
    asset,
    vault_id,
):
    action_id = switchboard_golf.addAsset(
        asset,
        [vault_id],
        0,
        0,
        1_000 * EIGHTEEN_DECIMALS,
        10_000 * EIGHTEEN_DECIMALS,
        0,
        (0, 0, 0, 0, 0, 0),
        False,
        False,
        False,
        True,
        False,
        True,
        False,
        True,
        True,
        True,
        0,
        (False, 0, 0, 0, 0),
        ZERO_ADDRESS,
        False,
        sender=governance.address,
    )
    _execute(switchboard_golf, governance, action_id)


def _prepare_promotional_asset(
    switchboard_golf,
    governance,
    mission_control,
    asset,
    vault_id,
):
    _add_promotional_asset(
        switchboard_golf,
        governance,
        asset,
        vault_id,
    )
    assert mission_control.rewardVaultId(asset) == vault_id
    config = mission_control.assetConfig(asset)
    assert not config.canDeposit
    assert config.debtTerms.ltv == 0
    assert config.stakersPointsAlloc == 0
    assert config.voterPointsAlloc == 0
    assert mission_control.accrualStartBlock(asset, vault_id) == 0


def _prepare_collection(
    switchboard_bravo,
    governance,
    asset,
    vault_id,
    testers=None,
):
    action_id = switchboard_bravo.preparePromotionalCollection(
        asset,
        vault_id,
        testers or [],
        sender=governance.address,
    )
    _execute(switchboard_bravo, governance, action_id)


def _start_deposit_allocs(
    switchboard_bravo,
    governance,
    mission_control,
    asset,
    stakers,
    voter,
):
    live = mission_control.assetConfig(asset)
    return switchboard_bravo.setAssetDepositParams(
        asset,
        list(live.vaultIds),
        stakers,
        voter,
        live.perUserDepositLimit,
        live.globalDepositLimit,
        live.minDepositBalance,
        sender=governance.address,
    )


def _set_deposit_allocs(
    switchboard_bravo,
    governance,
    mission_control,
    asset,
    stakers,
    voter,
):
    action_id = _start_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        asset,
        stakers,
        voter,
    )
    _execute(switchboard_bravo, governance, action_id)


def _open_deposits(switchboard_charlie, governance, asset):
    assert switchboard_charlie.setCanDepositAsset(
        asset,
        True,
        sender=governance.address,
    )


def _update_points(lootbox, teller, user, vault_id, vault, asset):
    lootbox.updateDepositPoints(
        user,
        vault_id,
        vault,
        asset,
        sender=teller.address,
    )


def _assert_point_buckets_clear(points):
    assert points.balancePoints == 0
    assert points.ripeStakerPoints == 0
    assert points.ripeVotePoints == 0
    assert points.ripeGenPoints == 0


def test_prepare_collection_resets_tester_without_withdrawal(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=12)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    assert ledger.userDepositPoints(bob, vault_id, bravo_token).balancePoints > 0

    action_id = switchboard_bravo.preparePromotionalCollection(
        bravo_token,
        vault_id,
        [bob],
        sender=governance.address,
    )
    assert not mission_control.assetConfig(bravo_token).canDeposit
    _execute(switchboard_bravo, governance, action_id)

    config = mission_control.assetConfig(bravo_token)
    points = ledger.assetDepositPoints(vault_id, bravo_token)
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256
    assert config.voterPointsAlloc == 0
    assert not config.canDeposit
    assert points.lastBalance != 0
    _assert_point_buckets_clear(points)
    assert points.lastUsdValue == 0
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints


def test_prepare_collection_allows_empty_tester_list_when_clear(
    switchboard_bravo,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )

    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
        [],
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_prepare_collection_omitted_tester_fails_closed(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    alice,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=10)
    performDeposit(
        alice,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=10)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    _update_points(
        lootbox,
        teller,
        alice,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    assert ledger.userDepositPoints(bob, vault_id, bravo_token).balancePoints > 0
    assert ledger.userDepositPoints(alice, vault_id, bravo_token).balancePoints > 0

    action_id = switchboard_bravo.preparePromotionalCollection(
        bravo_token,
        vault_id,
        [alice],
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    with boa.reverts("promotional points not clear"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )
    assert switchboard_bravo.hasPendingAction(action_id)
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0


def test_prepare_collection_rejects_zero_or_duplicate_testers(
    switchboard_bravo,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bob,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )

    with boa.reverts("invalid tester"):
        switchboard_bravo.preparePromotionalCollection(
            bravo_token,
            vault_id,
            [ZERO_ADDRESS],
            sender=governance.address,
        )
    with boa.reverts("duplicate tester"):
        switchboard_bravo.preparePromotionalCollection(
            bravo_token,
            vault_id,
            [bob, bob],
            sender=governance.address,
        )


def test_prepare_collection_cancel_leaves_deposits_off(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _open_deposits(switchboard_charlie, governance, bravo_token)

    action_id = switchboard_bravo.preparePromotionalCollection(
        bravo_token,
        vault_id,
        [],
        sender=governance.address,
    )
    assert not mission_control.assetConfig(bravo_token).canDeposit
    assert switchboard_bravo.cancelPendingAction(
        action_id,
        sender=governance.address,
    )
    assert not switchboard_bravo.hasPendingAction(action_id)
    assert not mission_control.assetConfig(bravo_token).canDeposit
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0


def test_prepare_collection_is_idempotent_when_deposits_already_off(
    switchboard_bravo,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    assert not mission_control.assetConfig(bravo_token).canDeposit

    action_id = switchboard_bravo.preparePromotionalCollection(
        bravo_token,
        vault_id,
        [],
        sender=governance.address,
    )
    assert switchboard_bravo.hasPendingAction(action_id)
    assert not mission_control.assetConfig(bravo_token).canDeposit
    _execute(switchboard_bravo, governance, action_id)
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_prepare_collection_clears_post_arm_usd_weight(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    global_before = ledger.globalDepositPoints()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    funded_asset = ledger.assetDepositPoints(vault_id, bravo_token)
    funded_global = ledger.globalDepositPoints()
    asset_usd = funded_asset.lastUsdValue
    assert asset_usd > 0
    assert funded_global.lastUsdValue == global_before.lastUsdValue + asset_usd
    assert mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints

    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
        [bob],
    )
    armed_asset = ledger.assetDepositPoints(vault_id, bravo_token)
    armed_global = ledger.globalDepositPoints()
    assert armed_asset.lastUsdValue == 0
    assert armed_global.lastUsdValue == funded_global.lastUsdValue - asset_usd
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints


def test_frozen_row_does_not_fund_global_gen_over_many_blocks(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    funded = ledger.assetDepositPoints(vault_id, bravo_token)
    assert funded.lastUsdValue > 0
    old_asset_usd = funded.lastUsdValue

    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
        [bob],
    )
    armed_asset = ledger.assetDepositPoints(vault_id, bravo_token)
    armed_global = ledger.globalDepositPoints()
    assert armed_asset.lastUsdValue == 0

    elapsed = 25
    boa.env.time_travel(blocks=elapsed)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    later_asset = ledger.assetDepositPoints(vault_id, bravo_token)
    later_global = ledger.globalDepositPoints()
    assert later_asset.ripeGenPoints == 0
    assert later_asset.lastUsdValue == 0
    assert later_global.lastUsdValue == armed_global.lastUsdValue
    assert later_global.ripeGenPoints == (
        armed_global.ripeGenPoints + armed_global.lastUsdValue * elapsed
    )
    assert later_global.ripeGenPoints != (
        armed_global.ripeGenPoints
        + (armed_global.lastUsdValue + old_asset_usd) * elapsed
    )


def test_prepare_collection_clears_live_voter_row(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0
    boa.env.time_travel(blocks=12)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    before = ledger.assetDepositPoints(vault_id, bravo_token)
    assert before.balancePoints > 0
    assert before.ripeVotePoints > 0

    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
        [bob],
    )
    after = ledger.assetDepositPoints(vault_id, bravo_token)
    assert mission_control.assetConfig(bravo_token).voterPointsAlloc == 0
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256
    _assert_point_buckets_clear(after)
    assert after.lastUsdValue == 0


def test_deposits_under_max_accrue_no_points_or_usd_weight(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    global_before = ledger.globalDepositPoints()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=20)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )

    points = ledger.assetDepositPoints(vault_id, bravo_token)
    user_points = ledger.userDepositPoints(bob, vault_id, bravo_token)
    global_after = ledger.globalDepositPoints()
    assert points.lastBalance > 0
    assert user_points.lastBalance > 0
    _assert_point_buckets_clear(points)
    assert user_points.balancePoints == 0
    assert points.lastUsdValue == 0
    assert global_after.lastUsdValue == global_before.lastUsdValue


def test_second_user_can_deposit_during_collection_without_bravo_alloc_change(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    alice,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    ledger,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    performDeposit(
        alice,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )

    assert ledger.userDepositPoints(bob, vault_id, bravo_token).lastBalance > 0
    assert ledger.userDepositPoints(alice, vault_id, bravo_token).lastBalance > 0
    config = mission_control.assetConfig(bravo_token)
    assert config.stakersPointsAlloc == 0
    assert config.voterPointsAlloc == 0
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_nonzero_voter_allocation_writes_activation_block(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    ledger,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )

    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    start_block = mission_control.accrualStartBlock(bravo_token, vault_id)
    assert start_block == boa.env.evm.patch.block_number
    assert start_block not in (0, MAX_UINT256)
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints
    assert ledger.assetDepositPoints(vault_id, bravo_token).lastUsdValue == 0


def test_nonzero_voter_allocation_requires_collection_balance(
    switchboard_bravo,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )

    action_id = _start_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    with boa.reverts("promotional row has no balance"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )
    assert switchboard_bravo.hasPendingAction(action_id)
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_voter_allocation_is_permanent_after_activation(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )

    action_id = _start_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        21,
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    with boa.reverts("promotional voter alloc is permanent"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )
    config = mission_control.assetConfig(bravo_token)
    assert config.voterPointsAlloc == 20
    assert config.stakersPointsAlloc == 0


def test_zero_voter_bravo_write_works_while_armed(
    switchboard_bravo,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
    )
    live = mission_control.assetConfig(bravo_token)
    new_per_user_limit = live.perUserDepositLimit + EIGHTEEN_DECIMALS
    action_id = switchboard_bravo.setAssetDepositParams(
        bravo_token,
        list(live.vaultIds),
        0,
        0,
        new_per_user_limit,
        live.globalDepositLimit,
        live.minDepositBalance,
        sender=governance.address,
    )
    _execute(switchboard_bravo, governance, action_id)

    config = mission_control.assetConfig(bravo_token)
    assert config.perUserDepositLimit == new_per_user_limit
    assert config.voterPointsAlloc == 0
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_full_operator_walk_starts_tickets_at_activation_only(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    alice,
    bob,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
    mock_price_source,
):
    setGeneralConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _open_deposits(switchboard_charlie, governance, bravo_token)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=12)
    _update_points(
        lootbox,
        teller,
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    assert ledger.userDepositPoints(bob, vault_id, bravo_token).balancePoints > 0
    teller.withdraw(
        bravo_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    )

    _prepare_collection(
        switchboard_bravo,
        governance,
        bravo_token,
        vault_id,
        [bob],
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256
    _open_deposits(switchboard_charlie, governance, bravo_token)
    performDeposit(
        alice,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=24)
    _update_points(
        lootbox,
        teller,
        alice,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    collection_points = ledger.userDepositPoints(alice, vault_id, bravo_token)
    assert collection_points.lastBalance > 0
    assert collection_points.balancePoints == 0

    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    start_block = mission_control.accrualStartBlock(bravo_token, vault_id)
    assert start_block == boa.env.evm.patch.block_number
    at_activation = ledger.userDepositPoints(alice, vault_id, bravo_token)
    assert at_activation.balancePoints == 0

    elapsed = 12
    boa.env.time_travel(blocks=elapsed)
    _update_points(
        lootbox,
        teller,
        alice,
        vault_id,
        simple_erc20_vault,
        bravo_token,
    )
    after_activation = ledger.userDepositPoints(alice, vault_id, bravo_token)
    assert after_activation.balancePoints == after_activation.lastBalance * elapsed
