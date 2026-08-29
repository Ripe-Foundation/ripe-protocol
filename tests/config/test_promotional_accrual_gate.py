import boa

from conf_utils import filter_logs
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


def _arm_promotional_asset(
    switchboard_foxtrot,
    governance,
    asset,
    vault_id,
    should_arm=True,
):
    action_id = switchboard_foxtrot.setAccrualClockArmed(
        asset,
        vault_id,
        should_arm,
        sender=governance.address,
    )
    _execute(switchboard_foxtrot, governance, action_id)


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


def _set_deposit_allocs(switchboard_bravo, governance, mission_control, asset, stakers, voter):
    live = mission_control.assetConfig(asset)
    action_id = switchboard_bravo.setAssetDepositParams(
        asset,
        list(live.vaultIds),
        stakers,
        voter,
        live.perUserDepositLimit,
        live.globalDepositLimit,
        live.minDepositBalance,
        sender=governance.address,
    )
    _execute(switchboard_bravo, governance, action_id)


def test_foxtrot_emits_accrual_clock_events(
    switchboard_golf,
    switchboard_foxtrot,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    armed = filter_logs(switchboard_foxtrot, "AccrualClockArmedSet")
    assert len(armed) >= 1
    assert armed[-1].asset == bravo_token.address
    assert armed[-1].vaultId == vault_id
    assert armed[-1].shouldArm

    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
        False,
    )
    disarmed = filter_logs(switchboard_foxtrot, "AccrualClockArmedSet")
    assert len(disarmed) >= 1
    assert disarmed[-1].asset == bravo_token.address
    assert disarmed[-1].vaultId == vault_id
    assert not disarmed[-1].shouldArm


def test_promotional_clock_can_cancel_only_before_collection_opens(
    switchboard_golf,
    switchboard_foxtrot,
    switchboard_charlie,
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

    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256

    with boa.reverts("armed promotional ltv must remain zero"):
        switchboard_golf.setAssetDebtTerms(
            bravo_token,
            30_00,
            50_00,
            70_00,
            10_00,
            5_00,
            1_00,
            sender=governance.address,
        )

    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
        False,
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0

    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    with boa.reverts("deposits must be disabled"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            False,
            sender=governance.address,
        )


def test_armed_deposits_refresh_balances_without_points_or_price(
    switchboard_golf,
    switchboard_foxtrot,
    switchboard_charlie,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )

    global_before = ledger.globalDepositPoints()
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )

    asset_points = ledger.assetDepositPoints(vault_id, bravo_token)
    user_points = ledger.userDepositPoints(bob, vault_id, bravo_token)
    global_after = ledger.globalDepositPoints()
    assert asset_points.lastBalance > 0
    assert user_points.lastBalance > 0
    assert asset_points.lastUpdate == boa.env.evm.patch.block_number
    assert user_points.lastUpdate == boa.env.evm.patch.block_number
    assert asset_points.balancePoints == 0
    assert user_points.balancePoints == 0
    assert asset_points.ripeStakerPoints == 0
    assert asset_points.ripeVotePoints == 0
    assert asset_points.ripeGenPoints == 0
    assert asset_points.lastUsdValue == 0
    assert global_after.lastUsdValue == global_before.lastUsdValue
    assert global_after.ripeGenPoints == global_before.ripeGenPoints

    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        False,
        sender=governance.address,
    )
    with boa.reverts("asset points not pristine"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            False,
            sender=governance.address,
        )


def test_voter_allocation_activates_and_permanently_protects_campaign(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_foxtrot,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )

    live = mission_control.assetConfig(bravo_token)
    activation = switchboard_bravo.setAssetDepositParams(
        bravo_token,
        list(live.vaultIds),
        0,
        20,
        live.perUserDepositLimit,
        live.globalDepositLimit,
        live.minDepositBalance,
        sender=governance.address,
    )
    _execute(switchboard_bravo, governance, activation)
    start_block = mission_control.accrualStartBlock(bravo_token, vault_id)
    assert start_block == boa.env.evm.patch.block_number
    assert start_block not in (0, MAX_UINT256)
    assert mission_control.assetConfig(bravo_token).voterPointsAlloc == 20
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints

    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    asset_points = ledger.assetDepositPoints(vault_id, bravo_token)
    user_points = ledger.userDepositPoints(bob, vault_id, bravo_token)
    assert asset_points.balancePoints > 0
    assert user_points.balancePoints > 0
    assert asset_points.ripeVotePoints > 0
    assert asset_points.ripeStakerPoints == 0
    assert asset_points.ripeGenPoints == 0
    assert asset_points.lastUsdValue == 0

    voter_change = switchboard_bravo.setAssetDepositParams(
        bravo_token,
        list(live.vaultIds),
        0,
        21,
        live.perUserDepositLimit,
        live.globalDepositLimit,
        live.minDepositBalance,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    with boa.reverts("promotional voter alloc is permanent"):
        switchboard_bravo.executePendingAction(
            voter_change,
            sender=governance.address,
        )
    assert switchboard_bravo.hasPendingAction(voter_change)

    debt_terms = (30_00, 50_00, 70_00, 10_00, 5_00, 1_00)
    debt_action = switchboard_golf.setAssetDebtTerms(
        bravo_token,
        *debt_terms,
        sender=governance.address,
    )
    _execute(switchboard_golf, governance, debt_action)
    assert mission_control.assetConfig(bravo_token).debtTerms == debt_terms
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == start_block

    with boa.reverts("promotional reward row migration required"):
        switchboard_charlie.setRewardVaultId(
            bravo_token,
            0,
            sender=governance.address,
        )

    deregister = switchboard_charlie.deregisterAsset(
        bravo_token,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    with boa.reverts("promotional campaign cannot deregister"):
        switchboard_charlie.executePendingAction(
            deregister,
            sender=governance.address,
        )


def test_empty_checkpoint_blocks_arm(
    switchboard_charlie,
    switchboard_foxtrot,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
    mock_price_source,
    ledger,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert switchboard_charlie.checkpointAssetDepositPointsAt(
        bravo_token,
        vault_id,
        simple_erc20_vault,
        sender=governance.address,
    )
    points = ledger.assetDepositPoints(vault_id, bravo_token)
    assert points.lastUpdate != 0
    assert points.lastBalance == 0
    assert points.ripeGenPoints == 0
    assert points.lastUsdValue == 0

    with boa.reverts("asset points not pristine"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            True,
            sender=governance.address,
        )


def test_update_many_rejects_zero_address(
    switchboard_charlie,
    switchboard_foxtrot,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    simple_erc20_vault,
    vault_book,
    ledger,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _prepare_promotional_asset(
        switchboard_golf,
        governance,
        mission_control,
        bravo_token,
        vault_id,
    )
    with boa.reverts("invalid user"):
        switchboard_charlie.updateManyDepositPoints(
            [ZERO_ADDRESS],
            vault_id,
            bravo_token,
            sender=governance.address,
        )
    assert ledger.assetDepositPoints(vault_id, bravo_token).lastUpdate == 0

    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256


def test_armed_reward_row_rejects_empty_checkpoint(
    switchboard_charlie,
    switchboard_foxtrot,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    with boa.reverts("cannot checkpoint armed promotional row"):
        switchboard_charlie.checkpointAssetDepositPointsAt(
            bravo_token,
            vault_id,
            simple_erc20_vault,
            sender=governance.address,
        )


def test_deregister_clears_reward_row_clock(
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
    mission_control.setAccrualStartBlock(
        bravo_token,
        vault_id,
        MAX_UINT256,
        sender=switchboard_bravo.address,
    )
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == MAX_UINT256
    assert mission_control.deregisterAsset(
        bravo_token,
        sender=switchboard_charlie.address,
    )
    assert not mission_control.isSupportedAsset(bravo_token)
    assert mission_control.rewardVaultId(bravo_token) == 0
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0


def test_deposit_then_full_withdraw_cannot_disarm(
    switchboard_charlie,
    switchboard_foxtrot,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    teller.withdraw(bravo_token, amount, bob, simple_erc20_vault, sender=bob)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    points = ledger.assetDepositPoints(vault_id, bravo_token)
    assert points.lastUpdate != 0
    assert points.lastBalance == 0
    assert points.ripeGenPoints == 0
    assert points.lastUsdValue == 0
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        False,
        sender=governance.address,
    )

    with boa.reverts("asset points not pristine"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            False,
            sender=governance.address,
        )


def test_accrued_gen_points_still_block_arm(
    switchboard_charlie,
    switchboard_foxtrot,
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
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    teller.withdraw(bravo_token, amount, bob, simple_erc20_vault, sender=bob)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    points = ledger.assetDepositPoints(vault_id, bravo_token)
    assert points.lastBalance == 0
    assert points.lastUsdValue == 0
    assert points.ripeGenPoints > 0
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        False,
        sender=governance.address,
    )

    with boa.reverts("asset points not pristine"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            True,
            sender=governance.address,
        )


def test_voter_zero_crossing_settles_gen_usd(
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
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    global_before = ledger.globalDepositPoints()
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    asset_funded = ledger.assetDepositPoints(vault_id, bravo_token)
    global_funded = ledger.globalDepositPoints()
    asset_usd = asset_funded.lastUsdValue
    assert asset_usd > 0
    assert global_funded.lastUsdValue == global_before.lastUsdValue + asset_usd
    assert mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints

    boa.env.time_travel(blocks=10)
    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    assert mission_control.assetConfig(bravo_token).voterPointsAlloc == 20
    assert mission_control.accrualStartBlock(bravo_token, vault_id) == 0
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints
    asset_off = ledger.assetDepositPoints(vault_id, bravo_token)
    global_off = ledger.globalDepositPoints()
    assert asset_off.lastUsdValue == 0
    assert global_off.lastUsdValue == global_funded.lastUsdValue - asset_usd
    gen_at_off = asset_off.ripeGenPoints
    assert gen_at_off == asset_funded.ripeGenPoints + asset_usd * (
        asset_off.lastUpdate - asset_funded.lastUpdate
    )

    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    asset_stale = ledger.assetDepositPoints(vault_id, bravo_token)
    global_stale = ledger.globalDepositPoints()
    assert asset_stale.lastUsdValue == 0
    assert asset_stale.ripeGenPoints == gen_at_off
    assert global_stale.lastUsdValue == global_off.lastUsdValue
    assert global_stale.ripeGenPoints == global_off.ripeGenPoints + (
        global_off.lastUsdValue * 20
    )

    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        0,
    )
    assert mission_control.assetConfig(bravo_token).voterPointsAlloc == 0
    assert mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints
    asset_on = ledger.assetDepositPoints(vault_id, bravo_token)
    global_on = ledger.globalDepositPoints()
    assert asset_on.lastUsdValue == asset_usd
    assert global_on.lastUsdValue == global_funded.lastUsdValue
    gen_at_on = asset_on.ripeGenPoints
    assert gen_at_on == gen_at_off

    elapsed = 7
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    asset_later = ledger.assetDepositPoints(vault_id, bravo_token)
    global_later = ledger.globalDepositPoints()
    assert asset_later.lastUsdValue == asset_usd
    assert asset_later.ripeGenPoints == gen_at_on + asset_usd * elapsed
    assert global_later.lastUsdValue == global_funded.lastUsdValue
    assert global_later.ripeGenPoints == global_on.ripeGenPoints + (
        global_on.lastUsdValue * elapsed
    )


def test_staggered_depositors_share_post_activation_elapsed(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_foxtrot,
    switchboard_golf,
    governance,
    mission_control,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    simple_erc20_vault,
    vault_book,
    performDeposit,
    lootbox,
    ledger,
    teller,
    setGeneralConfig,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=15)
    performDeposit(
        alice,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=10)

    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    start_block = mission_control.accrualStartBlock(bravo_token, vault_id)
    assert start_block not in (0, MAX_UINT256)
    bob_before = ledger.userDepositPoints(bob, vault_id, bravo_token)
    alice_before = ledger.userDepositPoints(alice, vault_id, bravo_token)
    assert bob_before.lastUpdate < start_block
    assert alice_before.lastUpdate < start_block
    assert bob_before.lastUpdate < alice_before.lastUpdate
    assert bob_before.balancePoints == 0
    assert alice_before.balancePoints == 0

    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    lootbox.updateDepositPoints(
        alice,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    bob_after = ledger.userDepositPoints(bob, vault_id, bravo_token)
    alice_after = ledger.userDepositPoints(alice, vault_id, bravo_token)
    asset_after = ledger.assetDepositPoints(vault_id, bravo_token)
    assert bob_after.balancePoints == alice_after.balancePoints
    assert bob_after.balancePoints == bob_after.lastBalance * elapsed
    assert alice_after.balancePoints == alice_after.lastBalance * elapsed
    assert (
        bob_after.balancePoints + alice_after.balancePoints
        <= asset_after.balancePoints
    )
    assert asset_after.balancePoints == asset_after.lastBalance * elapsed


def test_priced_armed_and_live_row_does_not_fund_gen(
    switchboard_bravo,
    switchboard_charlie,
    switchboard_foxtrot,
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
    _arm_promotional_asset(
        switchboard_foxtrot,
        governance,
        bravo_token,
        vault_id,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token,
        True,
        sender=governance.address,
    )
    global_before = ledger.globalDepositPoints()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=12)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    armed_points = ledger.assetDepositPoints(vault_id, bravo_token)
    armed_global = ledger.globalDepositPoints()
    assert armed_points.lastBalance > 0
    assert armed_points.lastUsdValue == 0
    assert armed_points.ripeGenPoints == 0
    assert armed_points.ripeVotePoints == 0
    assert armed_global.lastUsdValue == global_before.lastUsdValue

    _set_deposit_allocs(
        switchboard_bravo,
        governance,
        mission_control,
        bravo_token,
        0,
        20,
    )
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        bravo_token,
        sender=teller.address,
    )
    live_points = ledger.assetDepositPoints(vault_id, bravo_token)
    live_global = ledger.globalDepositPoints()
    assert live_points.balancePoints > 0
    assert live_points.ripeVotePoints > 0
    assert live_points.ripeGenPoints == 0
    assert live_points.lastUsdValue == 0
    assert live_global.lastUsdValue == global_before.lastUsdValue
    assert not mission_control.getDepositPointsConfig(
        bravo_token,
        vault_id,
    ).shouldFundGenPoints
