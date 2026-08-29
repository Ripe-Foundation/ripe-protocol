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


def test_non_pristine_reward_row_cannot_arm(
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
    assert ledger.assetDepositPoints(vault_id, bravo_token).lastUpdate != 0

    with boa.reverts("asset points not pristine"):
        switchboard_foxtrot.setAccrualClockArmed(
            bravo_token,
            vault_id,
            True,
            sender=governance.address,
        )
