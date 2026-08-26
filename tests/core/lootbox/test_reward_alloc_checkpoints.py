import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


EIP170_LIMIT = 24_576

_CHARLIE_BRAVO_BATCH = """
# pragma version ~=0.4.3

interface Charlie:
    def checkpointAssetDepositPointsAt(_asset: address, _vaultId: uint256, _vaultAddr: address) -> bool: nonpayable

interface Bravo:
    def executePendingAction(_actionId: uint256) -> bool: nonpayable

@external
def run(
    _charlie: address,
    _bravo: address,
    _asset: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _actionId: uint256,
):
    extcall Charlie(_charlie).checkpointAssetDepositPointsAt(_asset, _vaultId, _vaultAddr)
    extcall Bravo(_bravo).executePendingAction(_actionId)
"""

_COMPAT_VAULT = """
# pragma version ~=0.4.3

@external
@view
def getTotalAmountForVault(_asset: address) -> uint256:
    return 100 * 10**18

@external
@view
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return 0

@external
@view
def totalBalances(_asset: address) -> uint256:
    return 100 * 10**18
"""


def _charlie_bravo_batch(
    governance,
    charlie,
    bravo,
    asset,
    vault_id,
    vault_addr,
    action_id,
):
    impl = boa.loads(_CHARLIE_BRAVO_BATCH, name="charlie_bravo_batch")
    prev = boa.env.get_code(governance.address)
    boa.env.set_code(governance.address, impl.env.get_code(impl.address))
    try:
        return impl.deployer.at(governance.address).run(
            charlie.address,
            bravo.address,
            asset,
            vault_id,
            vault_addr,
            action_id,
        )
    finally:
        boa.env.set_code(governance.address, prev)


def _assert_ripe_delta(ledger, avail_before, last_update_before, ripe_per_block):
    elapsed = ledger.ripeRewards().lastUpdate - last_update_before
    expected = min(elapsed * ripe_per_block, avail_before)
    assert ledger.ripeAvailForRewards() == avail_before - expected
    return expected


def _points_tuple(points):
    return (
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
    )


def _walk_children(computation):
    for child in getattr(computation, "children", []) or []:
        yield child
        yield from _walk_children(child)


def _count_calls(computation, address, selector):
    expected = bytes.fromhex(str(address)[2:])
    return sum(
        getattr(child.msg, "code_address", None) == expected
        and bytes(child.msg.data[:4]) == selector
        for child in _walk_children(computation)
    )


def _execute(switchboard, governance, action_id):
    boa.env.time_travel(blocks=max(switchboard.actionTimeLock(), 1))
    assert switchboard.executePendingAction(action_id, sender=governance.address)


def _queue_deposit_params(
    switchboard_bravo,
    governance,
    asset,
    vault_ids,
    stakers,
    voters,
    per_user=2_000 * EIGHTEEN_DECIMALS,
    global_limit=20_000 * EIGHTEEN_DECIMALS,
    min_deposit=0,
    mission_control=ZERO_ADDRESS,
):
    return switchboard_bravo.setAssetDepositParams(
        asset,
        vault_ids,
        stakers,
        voters,
        per_user,
        global_limit,
        min_deposit,
        mission_control,
        sender=governance.address,
    )


def _seed_live_asset(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    asset,
    vault_ids,
    stakers=0,
    voters=0,
    points_enabled=True,
):
    setGeneralConfig()
    setRipeRewardsConfig(points_enabled, 10, 25_00, 25_00, 25_00, 25_00)
    setAssetConfig(
        asset,
        _vaultIds=vault_ids,
        _stakersPointsAlloc=stakers,
        _voterPointsAlloc=voters,
        _perUserDepositLimit=2_000 * EIGHTEEN_DECIMALS,
        _globalDepositLimit=20_000 * EIGHTEEN_DECIMALS,
    )


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


@pytest.mark.parametrize(
    ("old_stakers", "old_voters", "new_stakers", "new_voters"),
    [
        (0, 20, 0, 8),
        (10, 0, 25, 0),
    ],
)
def test_live_alloc_change_settles_old_interval(
    old_stakers,
    old_voters,
    new_stakers,
    new_voters,
    alpha_token,
    ripe_token,
    ripe_gov_vault,
    simple_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
    bob,
    whale,
    switchboard_alpha,
    mission_control,
):
    if old_stakers or new_stakers:
        vault_id = 2
        vault_addr = ripe_gov_vault
        asset = ripe_token
        setGeneralConfig()
        setRipeRewardsConfig(True, 10, 25_00, 25_00, 25_00, 25_00)
        setAssetConfig(
            asset,
            _vaultIds=[vault_id],
            _stakersPointsAlloc=old_stakers,
            _voterPointsAlloc=old_voters,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            100_00,
            False,
            (100, 1_000, 100_00, False, 0),
            sender=switchboard_alpha.address,
        )
        mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
        amount = 100 * EIGHTEEN_DECIMALS
        ripe_token.transfer(bob, amount, sender=whale)
        ripe_token.approve(teller, amount, sender=bob)
        teller.depositIntoGovVault(ripe_token, amount, 100, bob, sender=bob)
        lootbox.updateDepositPoints(bob, vault_id, vault_addr, asset, sender=teller.address)
    else:
        vault_id = vault_book.getRegId(simple_erc20_vault)
        vault_addr = simple_erc20_vault
        asset = alpha_token
        _seed_live_asset(
            setGeneralConfig,
            setAssetConfig,
            setRipeRewardsConfig,
            asset,
            [vault_id],
            old_stakers,
            old_voters,
        )
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token)
        lootbox.updateDepositPoints(bob, vault_id, vault_addr, asset, sender=teller.address)

    before = ledger.assetDepositPoints(vault_id, asset)
    global_before = ledger.globalDepositPoints()
    totals_before = mission_control.getRewardsConfig()
    boa.env.time_travel(blocks=11)
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        asset,
        [vault_id],
        new_stakers,
        new_voters,
    )
    _execute(switchboard_bravo, governance, action_id)

    after = ledger.assetDepositPoints(vault_id, asset)
    elapsed = after.lastUpdate - before.lastUpdate
    assert after.lastUpdate == boa.env.evm.patch.block_number
    assert elapsed != 0
    assert after.ripeVotePoints == before.ripeVotePoints + old_voters * elapsed
    assert after.ripeStakerPoints == before.ripeStakerPoints + old_stakers * elapsed

    global_after = ledger.globalDepositPoints()
    global_elapsed = global_after.lastUpdate - global_before.lastUpdate
    assert global_before.lastUpdate != 0
    assert global_after.lastUpdate == after.lastUpdate
    assert global_elapsed == elapsed
    assert (
        global_after.ripeStakerPoints
        == global_before.ripeStakerPoints + totals_before.stakersPointsAllocTotal * global_elapsed
    )
    assert (
        global_after.ripeVotePoints
        == global_before.ripeVotePoints + totals_before.voterPointsAllocTotal * global_elapsed
    )

    later = 5
    boa.env.time_travel(blocks=later)
    lootbox.updateDepositPoints(ZERO_ADDRESS, vault_id, vault_addr, asset, sender=teller.address)
    latest = ledger.assetDepositPoints(vault_id, asset)
    assert latest.ripeVotePoints == after.ripeVotePoints + new_voters * later
    assert latest.ripeStakerPoints == after.ripeStakerPoints + new_stakers * later


@pytest.mark.parametrize("to_nonzero", [True, False])
def test_staker_zero_crossing_reclassifies_usd_without_post_pass_accrual(
    to_nonzero,
    ripe_token,
    ripe_gov_vault,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    switchboard_alpha,
    mission_control,
    governance,
    bob,
    whale,
):
    old_stakers = 0 if to_nonzero else 15
    new_stakers = 15 if to_nonzero else 0
    setGeneralConfig()
    setRipeRewardsConfig(True, 10, 25_00, 25_00, 25_00, 25_00)
    setAssetConfig(
        ripe_token,
        _vaultIds=[2],
        _stakersPointsAlloc=old_stakers,
        _voterPointsAlloc=0,
    )
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(bob, amount, sender=whale)
    ripe_token.approve(teller, amount, sender=bob)
    teller.depositIntoGovVault(ripe_token, amount, 100, bob, sender=bob)
    lootbox.updateDepositPoints(bob, 2, ripe_gov_vault, ripe_token, sender=teller.address)

    before = ledger.assetDepositPoints(2, ripe_token)
    boa.env.time_travel(blocks=9)
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        ripe_token,
        [2],
        new_stakers,
        0,
    )
    _execute(switchboard_bravo, governance, action_id)

    after = ledger.assetDepositPoints(2, ripe_token)
    elapsed = after.lastUpdate - before.lastUpdate
    assert after.lastUpdate == boa.env.evm.patch.block_number
    assert after.ripeStakerPoints == before.ripeStakerPoints + old_stakers * elapsed
    if to_nonzero:
        assert before.lastUsdValue != 0
        assert after.lastUsdValue == 0
    else:
        assert after.lastUsdValue != 0


def test_uninitialized_current_rows_are_skipped_and_empty_set_reverts(
    alpha_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
    bob,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_a, vault_b],
        12,
        0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 50 * EIGHTEEN_DECIMALS, alpha_token)
    lootbox.updateDepositPoints(
        bob, vault_a, simple_erc20_vault, alpha_token, sender=teller.address
    )
    assert ledger.assetDepositPoints(vault_b, alpha_token).lastUpdate == 0

    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_a, vault_b],
        0,
        0,
    )
    _execute(switchboard_bravo, governance, action_id)
    assert ledger.assetDepositPoints(vault_b, alpha_token).lastUpdate == 0
    assert ledger.assetDepositPoints(vault_a, alpha_token).lastUpdate != 0

    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_b],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    assert ledger.assetDepositPoints(vault_b, alpha_token).lastUpdate == 0
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_b],
        0,
        7,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    with boa.reverts("no initialized deposit points"):
        switchboard_bravo.executePendingAction(action_id, sender=governance.address)


def test_charlie_current_row_activation_then_bravo_zero_crossing_post_pass(
    ripe_token,
    ripe_gov_vault,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    switchboard_charlie,
    switchboard_alpha,
    mission_control,
    governance,
    mock_price_source,
    bob,
    whale,
):
    setGeneralConfig()
    setRipeRewardsConfig(True, 10, 25_00, 25_00, 25_00, 25_00)
    setAssetConfig(ripe_token, _vaultIds=[2], _stakersPointsAlloc=0, _voterPointsAlloc=0)
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    assert ledger.assetDepositPoints(2, ripe_token).lastUpdate == 0
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        ripe_token,
        [2],
        18,
        0,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))

    switchboard_alpha.setRewardsPointsEnabled(False, sender=governance.address)
    with boa.reverts("points disabled"):
        _charlie_bravo_batch(
            governance,
            switchboard_charlie,
            switchboard_bravo,
            ripe_token,
            2,
            ripe_gov_vault.address,
            action_id,
        )
    assert ledger.assetDepositPoints(2, ripe_token).lastUpdate == 0
    assert mission_control.assetConfig(ripe_token).stakersPointsAlloc == 0
    assert switchboard_bravo.hasPendingAction(action_id)

    switchboard_alpha.setRewardsPointsEnabled(True, sender=governance.address)
    _charlie_bravo_batch(
        governance,
        switchboard_charlie,
        switchboard_bravo,
        ripe_token,
        2,
        ripe_gov_vault.address,
        action_id,
    )
    after = ledger.assetDepositPoints(2, ripe_token)
    assert after.lastUpdate == boa.env.evm.patch.block_number
    assert after.lastUpdate != 0
    assert after.ripeStakerPoints == 0
    assert after.lastUsdValue == 0
    assert mission_control.assetConfig(ripe_token).stakersPointsAlloc == 18


def test_historical_charlie_pre_bravo_post_settles_old_then_new_rate(
    alpha_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    switchboard_charlie,
    mission_control,
    governance,
    bob,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_a],
        0,
        20,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 80 * EIGHTEEN_DECIMALS, alpha_token)
    lootbox.updateDepositPoints(
        bob, vault_a, simple_erc20_vault, alpha_token, sender=teller.address
    )

    zero_id = _queue_deposit_params(
        switchboard_bravo, governance, alpha_token, [vault_a], 0, 0
    )
    _execute(switchboard_bravo, governance, zero_id)
    move_id = _queue_deposit_params(
        switchboard_bravo, governance, alpha_token, [vault_b], 0, 0
    )
    _execute(switchboard_bravo, governance, move_id)
    switchboard_charlie.checkpointAssetDepositPointsAt(
        alpha_token,
        vault_b,
        rebase_erc20_vault.address,
        sender=governance.address,
    )
    enable_id = _queue_deposit_params(
        switchboard_bravo, governance, alpha_token, [vault_b], 0, 20
    )
    _execute(switchboard_bravo, governance, enable_id)

    # Close the untested window after the first post-move alloc change.
    switchboard_charlie.checkpointAssetDepositPointsAt(
        alpha_token,
        vault_a,
        simple_erc20_vault.address,
        sender=governance.address,
    )
    hist_before = ledger.assetDepositPoints(vault_a, alpha_token)
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_b],
        0,
        5,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 8))
    _charlie_bravo_batch(
        governance,
        switchboard_charlie,
        switchboard_bravo,
        alpha_token,
        vault_a,
        simple_erc20_vault.address,
        action_id,
    )
    hist_mid = ledger.assetDepositPoints(vault_a, alpha_token)
    assert hist_mid.ripeVotePoints == hist_before.ripeVotePoints + 20 * (
        hist_mid.lastUpdate - hist_before.lastUpdate
    )
    assert mission_control.assetConfig(alpha_token).voterPointsAlloc == 5

    later = 4
    boa.env.time_travel(blocks=later)
    switchboard_charlie.checkpointAssetDepositPointsAt(
        alpha_token,
        vault_a,
        simple_erc20_vault.address,
        sender=governance.address,
    )
    hist_after = ledger.assetDepositPoints(vault_a, alpha_token)
    assert hist_after.ripeVotePoints == hist_mid.ripeVotePoints + 5 * later


def test_points_disabled_live_alloc_change_does_not_move_last_update(
    alpha_token,
    simple_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    switchboard_alpha,
    governance,
    bob,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_id],
        0,
        20,
        points_enabled=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 20 * EIGHTEEN_DECIMALS, alpha_token)
    lootbox.updateDepositPoints(
        bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address
    )
    row_before = ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate
    global_before = ledger.globalDepositPoints().lastUpdate
    rewards_before = ledger.ripeRewards().lastUpdate

    switchboard_alpha.setRewardsPointsEnabled(False, sender=governance.address)
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        8,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    with boa.reverts("points disabled"):
        switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate == row_before
    assert ledger.globalDepositPoints().lastUpdate == global_before
    assert ledger.ripeRewards().lastUpdate == rewards_before


def test_staged_target_becomes_live_and_is_checkpointed(
    alpha_token,
    simple_erc20_vault,
    vault_book,
    ripe_hq,
    mission_control,
    defaults,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
    bob,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_id],
        0,
        20,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 25 * EIGHTEEN_DECIMALS, alpha_token)
    lootbox.updateDepositPoints(
        bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address
    )
    staged = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="alloc_staged_mc",
    )
    staged.setCoreRipeGovVaultId(2, sender=switchboard_bravo.address)
    staged.setAssetConfig(
        alpha_token,
        mission_control.assetConfig(alpha_token),
        sender=switchboard_bravo.address,
    )
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        9,
        mission_control=staged.address,
    )
    assert ripe_hq.startAddressUpdateToRegistry(5, staged, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(5, sender=governance.address)

    before = ledger.assetDepositPoints(vault_id, alpha_token)
    boa.env.time_travel(blocks=7)
    _execute(switchboard_bravo, governance, action_id)
    after = ledger.assetDepositPoints(vault_id, alpha_token)
    elapsed = after.lastUpdate - before.lastUpdate
    assert after.lastUpdate == boa.env.evm.patch.block_number
    assert after.ripeVotePoints == before.ripeVotePoints + 20 * elapsed
    assert staged.assetConfig(alpha_token).voterPointsAlloc == 9


def test_previously_live_bound_target_skips_checkpointing_when_staged(
    alpha_token,
    simple_erc20_vault,
    vault_book,
    ripe_hq,
    mission_control,
    defaults,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
    bob,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_id],
        0,
        20,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 25 * EIGHTEEN_DECIMALS, alpha_token)
    lootbox.updateDepositPoints(
        bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address
    )
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        4,
    )
    replacement = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="alloc_live_to_staged_mc",
    )
    assert ripe_hq.startAddressUpdateToRegistry(5, replacement, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(5, sender=governance.address)

    before = ledger.assetDepositPoints(vault_id, alpha_token)
    boa.env.time_travel(blocks=6)
    _execute(switchboard_bravo, governance, action_id)
    after = ledger.assetDepositPoints(vault_id, alpha_token)
    assert after.lastUpdate == before.lastUpdate
    assert after.ripeVotePoints == before.ripeVotePoints
    assert mission_control.assetConfig(alpha_token).voterPointsAlloc == 4
    assert not replacement.isSupportedAsset(alpha_token)


def test_legacy_unwind_gas_ten_initialized_rows(
    alpha_token,
    registerVault,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
):
    vault_ids = []
    for i in range(10):
        dummy = boa.loads(_COMPAT_VAULT, name=f"alloc_compat_vault_{i}")
        vault_ids.append(registerVault(dummy, f"Alloc Compat {i}"))
    assert len(vault_ids) == 10
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        vault_ids,
        20,
        0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    for vault_id in vault_ids:
        ledger.eval(
            f"self.assetDepositPoints[{vault_id}][{alpha_token.address}].lastUpdate = 1"
        )
        ledger.eval(
            f"self.assetDepositPoints[{vault_id}][{alpha_token.address}].lastBalance = {10**9}"
        )

    lootbox.updateRipeRewards(sender=teller.address)
    avail_before = ledger.ripeAvailForRewards()
    rewards_last_update_before = ledger.ripeRewards().lastUpdate
    ripe_per_block = 10

    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        vault_ids,
        0,
        0,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    gas_used = switchboard_bravo._computation.get_gas_used()
    selector = lootbox.updateDepositPoints.prepare_calldata(
        ZERO_ADDRESS, 1, ZERO_ADDRESS, alpha_token.address
    )[:4]
    lootbox_calls = _count_calls(
        switchboard_bravo._computation, lootbox.address, selector
    )
    print(
        f"LEGACY_UNWIND_GAS gas={gas_used} lootbox_calls={lootbox_calls}"
    )
    assert lootbox_calls == 20
    assert gas_used < 8_000_000
    _assert_ripe_delta(ledger, avail_before, rewards_last_update_before, ripe_per_block)


def test_bravo_selects_rows_by_last_update_field_order(
    alpha_token,
    bravo_token,
    simple_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    ledger,
    switchboard_bravo,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        alpha_token,
        [vault_id],
        0,
        0,
    )
    ledger.eval(
        f"self.assetDepositPoints[{vault_id}][{alpha_token.address}].lastUpdate = 1"
    )
    selected = ledger.assetDepositPoints(vault_id, alpha_token)
    assert selected.lastUpdate == 1
    assert selected.lastBalance == 0
    assert selected.ripeStakerPoints == 0
    assert selected.ripeVotePoints == 0
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        alpha_token,
        [vault_id],
        0,
        5,
    )
    _execute(switchboard_bravo, governance, action_id)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate != 0

    _seed_live_asset(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        bravo_token,
        [vault_id],
        0,
        0,
    )
    ledger.eval(
        f"self.assetDepositPoints[{vault_id}][{bravo_token.address}].lastBalance = 99"
    )
    ledger.eval(
        f"self.assetDepositPoints[{vault_id}][{bravo_token.address}].lastUsdValue = 99"
    )
    ledger.eval(
        f"self.assetDepositPoints[{vault_id}][{bravo_token.address}].ripeStakerPoints = 99"
    )
    ledger.eval(
        f"self.assetDepositPoints[{vault_id}][{bravo_token.address}].ripeVotePoints = 99"
    )
    skipped = ledger.assetDepositPoints(vault_id, bravo_token)
    assert skipped.lastUpdate == 0
    assert skipped.lastBalance == 99
    action_id = _queue_deposit_params(
        switchboard_bravo,
        governance,
        bravo_token,
        [vault_id],
        0,
        7,
    )
    boa.env.time_travel(blocks=max(switchboard_bravo.actionTimeLock(), 1))
    with boa.reverts("no initialized deposit points"):
        switchboard_bravo.executePendingAction(action_id, sender=governance.address)


def test_switchboard_runtimes_fit_eip170(
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
):
    sizes = {
        "SwitchboardAlpha": len(
            switchboard_alpha.env.get_code(switchboard_alpha.address)
        ),
        "SwitchboardBravo": len(
            switchboard_bravo.env.get_code(switchboard_bravo.address)
        ),
        "SwitchboardCharlie": len(
            switchboard_charlie.env.get_code(switchboard_charlie.address)
        ),
    }
    print("ALLOC_CHECKPOINT_DEPLOYED", sizes)
    print(
        "ALLOC_CHECKPOINT_HEADROOM",
        {name: EIP170_LIMIT - size for name, size in sizes.items()},
    )
    oversized = {name: size for name, size in sizes.items() if size > EIP170_LIMIT}
    assert not oversized, oversized
