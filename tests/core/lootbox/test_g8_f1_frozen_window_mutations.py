"""Group 8 F1 — frozen clocks/snapshots while loot points are off."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import clear_transient_storage, has_dev_reason
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


RIPE_PER_BLOCK = 9 * 10**15
DAY_IN_BLOCKS = 7200
YEAR_IN_BLOCKS = 365 * DAY_IN_BLOCKS
GOV_VAULT_ID = 2
SIMPLE_VAULT_ID = 3
ADMISSIBLE_VAULTS = [GOV_VAULT_ID, SIMPLE_VAULT_ID]


def _blk():
    return boa.env.evm.patch.block_number


@pytest.fixture(scope="module", autouse=True)
def _g8_vault_ids(vault_book, ripe_gov_vault, simple_erc20_vault):
    global GOV_VAULT_ID, SIMPLE_VAULT_ID, ADMISSIBLE_VAULTS
    GOV_VAULT_ID = vault_book.getRegId(ripe_gov_vault)
    SIMPLE_VAULT_ID = vault_book.getRegId(simple_erc20_vault)
    ADMISSIBLE_VAULTS = [GOV_VAULT_ID, SIMPLE_VAULT_ID]


@pytest.fixture(scope="module")
def launch_g8(
    _g8_vault_ids,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    ripe_token,
):
    def launch_g8(
        _stakersAlloc=90_00,
        _borrowersAlloc=10_00,
        _genDepositorsAlloc=0,
    ):
        setGeneralConfig(_canClaimLoot=True)
        setRipeRewardsConfig(
            _arePointsEnabled=True,
            _ripePerBlock=RIPE_PER_BLOCK,
            _borrowersAlloc=_borrowersAlloc,
            _stakersAlloc=_stakersAlloc,
            _votersAlloc=0,
            _genDepositorsAlloc=_genDepositorsAlloc,
            _autoStakeRatio=75_00,
            _autoStakeDurationRatio=33_00,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            100_00,
            False,
            (DAY_IN_BLOCKS, 3 * YEAR_IN_BLOCKS, 200_00, True, 80_00),
            sender=switchboard_alpha.address,
        )
        setAssetConfig(
            ripe_token,
            _vaultIds=[GOV_VAULT_ID],
            _stakersPointsAlloc=15_00,
            _voterPointsAlloc=0,
        )

    yield launch_g8


def _staker_row(setAssetConfig, token, _stakersPointsAlloc=15_00):
    setAssetConfig(
        token,
        _vaultIds=ADMISSIBLE_VAULTS,
        _stakersPointsAlloc=_stakersPointsAlloc,
        _voterPointsAlloc=0,
    )


def _credit_row(
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    mock_price_source,
    alpha_token,
    _stakersPointsAlloc=0,
):
    setAssetConfig(
        alpha_token,
        _vaultIds=ADMISSIBLE_VAULTS,
        _stakersPointsAlloc=_stakersPointsAlloc,
        _voterPointsAlloc=0,
        _debtTerms=createDebtTerms(_borrowRate=0, _daowry=0),
    )
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)


def _disable(switchboard_alpha, governance):
    switchboard_alpha.setRewardsPointsEnabled(False, sender=governance.address)


def _enable(switchboard_alpha, governance):
    switchboard_alpha.setRewardsPointsEnabled(True, sender=governance.address)


def _touch_dep(lootbox, teller, user, vault, asset, vault_id=SIMPLE_VAULT_ID):
    lootbox.updateDepositPoints(user, vault_id, vault, asset, sender=teller.address)


def _touch_bor(lootbox, teller, user):
    lootbox.updateBorrowPoints(user, sender=teller.address)


def _dep_snap(ledger, user, asset, vault_id=SIMPLE_VAULT_ID):
    return (
        ledger.userDepositPoints(user, vault_id, asset),
        ledger.assetDepositPoints(vault_id, asset),
        ledger.globalDepositPoints(),
    )


def _assert_dep_frozen(before, after):
    u0, a0, g0 = before
    u1, a1, g1 = after
    assert (u1.lastUpdate, u1.lastBalance, u1.balancePoints) == (
        u0.lastUpdate,
        u0.lastBalance,
        u0.balancePoints,
    )
    assert (a1.lastUpdate, a1.lastBalance, a1.lastUsdValue, a1.balancePoints) == (
        a0.lastUpdate,
        a0.lastBalance,
        a0.lastUsdValue,
        a0.balancePoints,
    )
    assert (
        g1.lastUpdate,
        g1.lastUsdValue,
        g1.ripeStakerPoints,
        g1.ripeVotePoints,
        g1.ripeGenPoints,
    ) == (
        g0.lastUpdate,
        g0.lastUsdValue,
        g0.ripeStakerPoints,
        g0.ripeVotePoints,
        g0.ripeGenPoints,
    )


def _bor_snap(ledger, user):
    return ledger.userBorrowPoints(user), ledger.globalBorrowPoints()


def _staker_loot(up, ap, gp, bucket):
    if 0 in (
        up.balancePoints,
        ap.balancePoints,
        ap.ripeStakerPoints,
        gp.ripeStakerPoints,
        bucket,
    ):
        return 0
    capped = min(ap.ripeStakerPoints, gp.ripeStakerPoints)
    return (bucket * capped // gp.ripeStakerPoints) * up.balancePoints // ap.balancePoints


def _assert_bor_frozen(before, after):
    u0, g0 = before
    u1, g1 = after
    assert (u1.lastUpdate, u1.lastPrincipal, u1.points) == (
        u0.lastUpdate,
        u0.lastPrincipal,
        u0.points,
    )
    assert (g1.lastUpdate, g1.lastPrincipal, g1.points) == (
        g0.lastUpdate,
        g0.lastPrincipal,
        g0.points,
    )


def test_g8_f1_withdraw_to_zero_credits_frozen_last_balance(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    frozen = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    start, lb = frozen.lastUpdate, frozen.lastBalance
    assert lb != 0
    boa.env.time_travel(blocks=20)
    before = _dep_snap(ledger, alice, alpha_token)
    _disable(switchboard_alpha, governance)
    teller.withdraw(alpha_token, MAX_UINT256, alice, simple_erc20_vault, sender=alice)
    _assert_dep_frozen(before, _dep_snap(ledger, alice, alpha_token))
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    after = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert after.balancePoints == lb * (_blk() - start)
    assert after.lastBalance == 0


def test_g8_f1_partial_withdraw_uses_pre_withdraw_last_balance(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    frozen = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    start, lb = frozen.lastUpdate, frozen.lastBalance
    boa.env.time_travel(blocks=20)
    before = _dep_snap(ledger, alice, alpha_token)
    _disable(switchboard_alpha, governance)
    teller.withdraw(
        alpha_token, 40 * EIGHTEEN_DECIMALS, alice, simple_erc20_vault, sender=alice
    )
    _assert_dep_frozen(before, _dep_snap(ledger, alice, alpha_token))
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    after = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert after.balancePoints == lb * (_blk() - start)
    assert after.lastBalance != lb
    assert after.lastBalance != 0


def test_g8_f1_deposit_more_uses_old_last_balance(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    frozen = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    start, lb = frozen.lastUpdate, frozen.lastBalance
    boa.env.time_travel(blocks=20)
    before = _dep_snap(ledger, alice, alpha_token)
    _disable(switchboard_alpha, governance)
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    _assert_dep_frozen(before, _dep_snap(ledger, alice, alpha_token))
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    after = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert after.balancePoints == lb * (_blk() - start)
    assert after.lastBalance != lb


def test_g8_f1_new_holder_while_disabled_gets_zero_on_first_enabled_touch(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    bob,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    a0 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    b0 = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    assert b0.lastUpdate == 0
    assert b0.lastBalance == 0
    assert b0.balancePoints == 0
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, bob, simple_erc20_vault, alpha_token)
    b1 = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    assert b1.balancePoints == 0
    assert b1.lastUpdate == _blk()
    assert b1.lastBalance != 0
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    a1 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert a1.balancePoints == a0.lastBalance * (_blk() - a0.lastUpdate)
    ap = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    assert ap.balancePoints == a1.balancePoints + b1.balancePoints


def test_g8_f1_borrow_repay_twins_use_frozen_last_principal(
    launch_g8,
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    green_token,
    alice,
    bob,
    sally,
    alpha_token,
):
    launch_g8(_borrowersAlloc=100_00, _stakersAlloc=0)
    _credit_row(
        setAssetConfig,
        createDebtTerms,
        setGeneralDebtConfig,
        mock_price_source,
        alpha_token,
    )
    performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(bob, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(sally, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    teller.borrow(50 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    teller.borrow(80 * EIGHTEEN_DECIMALS, sally, False, sender=sally)
    a0 = ledger.userBorrowPoints(alice)
    b0 = ledger.userBorrowPoints(bob)
    s0 = ledger.userBorrowPoints(sally)
    assert a0.lastPrincipal != 0 and b0.lastPrincipal != 0 and s0.lastPrincipal != 0
    boa.env.time_travel(blocks=20)

    before_a = _bor_snap(ledger, alice)
    _disable(switchboard_alpha, governance)
    green_token.approve(teller.address, MAX_UINT256, sender=alice)
    teller.repay(MAX_UINT256, alice, False, False, sender=alice)
    _assert_bor_frozen(before_a, _bor_snap(ledger, alice))
    _enable(switchboard_alpha, governance)
    _touch_bor(lootbox, teller, alice)
    a1 = ledger.userBorrowPoints(alice)
    assert a1.points == a0.lastPrincipal * (_blk() - a0.lastUpdate)
    assert a1.lastPrincipal == 0

    before_b = _bor_snap(ledger, bob)
    _disable(switchboard_alpha, governance)
    green_token.approve(teller.address, MAX_UINT256, sender=bob)
    teller.repay(20 * EIGHTEEN_DECIMALS, bob, False, False, sender=bob)
    _assert_bor_frozen(before_b, _bor_snap(ledger, bob))
    _enable(switchboard_alpha, governance)
    _touch_bor(lootbox, teller, bob)
    b1 = ledger.userBorrowPoints(bob)
    assert b1.points == b0.lastPrincipal * (_blk() - b0.lastUpdate)
    assert b1.lastPrincipal != b0.lastPrincipal
    assert b1.lastPrincipal != 0

    before_s = _bor_snap(ledger, sally)
    _disable(switchboard_alpha, governance)
    teller.borrow(20 * EIGHTEEN_DECIMALS, sally, False, sender=sally)
    _assert_bor_frozen(before_s, _bor_snap(ledger, sally))
    _enable(switchboard_alpha, governance)
    _touch_bor(lootbox, teller, sally)
    s1 = ledger.userBorrowPoints(sally)
    assert s1.points == s0.lastPrincipal * (_blk() - s0.lastUpdate)
    assert s1.lastPrincipal != s0.lastPrincipal


def test_g8_f1_two_disable_enable_cycles_do_not_bleed(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    a0 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    performDeposit(alice, 25 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    a1 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    first = a0.lastBalance * (_blk() - a0.lastUpdate)
    assert a1.balancePoints == first
    assert a1.lastBalance != a0.lastBalance
    lb1, lu1 = a1.lastBalance, a1.lastUpdate
    boa.env.time_travel(blocks=10)
    _disable(switchboard_alpha, governance)
    performDeposit(alice, 25 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    a2 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert a2.balancePoints == first + lb1 * (_blk() - lu1)


def test_g8_f1_claim_while_points_off_pays_stored_only(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    boa.env.time_travel(blocks=30)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    stored = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert stored.balancePoints != 0
    start, lb = stored.lastUpdate, stored.lastBalance
    boa.env.time_travel(blocks=10)
    _disable(switchboard_alpha, governance)
    before = _dep_snap(ledger, alice, alpha_token)
    pre_avail = ledger.ripeAvailForRewards()
    paid = teller.claimLoot(alice, False, sender=alice)
    clear_transient_storage()
    assert paid != 0
    after_claim = _dep_snap(ledger, alice, alpha_token)
    assert after_claim[0].balancePoints == 0
    assert after_claim[0].lastUpdate == start
    assert after_claim[0].lastBalance == lb
    assert after_claim[1].lastUpdate == before[1].lastUpdate
    assert after_claim[2].lastUpdate == before[2].lastUpdate
    assert ledger.ripeAvailForRewards() != pre_avail
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    credited = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert credited.balancePoints == lb * (_blk() - start)


def test_g8_f1_gen_last_usd_value_frozen_through_price_move(
    launch_g8,
    setAssetConfig,
    performDeposit,
    mock_price_source,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8(_stakersAlloc=0, _genDepositorsAlloc=100_00)
    _staker_row(setAssetConfig, alpha_token, _stakersPointsAlloc=0)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    before = _dep_snap(ledger, alice, alpha_token)
    assert before[1].lastUsdValue != 0
    usd = before[1].lastUsdValue
    start = before[1].lastUpdate
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    mock_price_source.setPrice(alpha_token, 5 * EIGHTEEN_DECIMALS)
    performDeposit(alice, 1 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    _assert_dep_frozen(before, _dep_snap(ledger, alice, alpha_token))
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    after = _dep_snap(ledger, alice, alpha_token)
    elapsed = _blk() - start
    assert after[1].ripeGenPoints == usd * elapsed
    assert after[2].ripeGenPoints == before[2].lastUsdValue * (
        _blk() - before[2].lastUpdate
    )


def test_g8_f1_reset_while_disabled_zeros_counters_then_span_credits(
    launch_g8,
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    switchboard_alpha,
    switchboard_delta,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8(_borrowersAlloc=10_00, _stakersAlloc=90_00)
    _credit_row(
        setAssetConfig,
        createDebtTerms,
        setGeneralDebtConfig,
        mock_price_source,
        alpha_token,
        _stakersPointsAlloc=15_00,
    )
    performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    teller.borrow(50 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    boa.env.time_travel(blocks=20)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    _touch_bor(lootbox, teller, alice)
    up0 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    ap0 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    bp0 = ledger.userBorrowPoints(alice)
    assert up0.balancePoints != 0
    assert ap0.ripeStakerPoints != 0
    assert bp0.points != 0
    _disable(switchboard_alpha, governance)
    lootbox.resetUserBalancePoints(
        alice, alpha_token, SIMPLE_VAULT_ID, sender=switchboard_delta.address
    )
    lootbox.resetAssetPoints(
        alpha_token, SIMPLE_VAULT_ID, sender=switchboard_delta.address
    )
    lootbox.resetUserBorrowPoints(alice, sender=switchboard_alpha.address)
    up1 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    ap1 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    bp1 = ledger.userBorrowPoints(alice)
    assert up1.balancePoints == 0
    assert ap1.ripeStakerPoints == 0
    assert bp1.points == 0
    assert up1.lastUpdate == up0.lastUpdate
    assert up1.lastBalance == up0.lastBalance
    assert ap1.lastUpdate == ap0.lastUpdate
    assert bp1.lastUpdate == bp0.lastUpdate
    assert bp1.lastPrincipal == bp0.lastPrincipal
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    _touch_bor(lootbox, teller, alice)
    up2 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    ap2 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    bp2 = ledger.userBorrowPoints(alice)
    assert up2.balancePoints == up0.lastBalance * (_blk() - up0.lastUpdate)
    assert ap2.ripeStakerPoints == 15_00 * (_blk() - ap0.lastUpdate)
    assert bp2.points == bp0.lastPrincipal * (_blk() - bp0.lastUpdate)


def test_g8_f1_two_staker_assets_honest_share_after_one_disabled_touch(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    _staker_row(setAssetConfig, bravo_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    a0 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    b0 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, bravo_token)
    g0 = ledger.globalDepositPoints()
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    performDeposit(alice, 1 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    clear_transient_storage()
    assert ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token).lastUpdate == a0.lastUpdate
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    _touch_dep(lootbox, teller, bob, simple_erc20_vault, bravo_token)
    ap = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    bp = ledger.assetDepositPoints(SIMPLE_VAULT_ID, bravo_token)
    gp = ledger.globalDepositPoints()
    assert ap.ripeStakerPoints == 15_00 * (_blk() - a0.lastUpdate)
    assert bp.ripeStakerPoints == 15_00 * (_blk() - b0.lastUpdate)
    assert gp.ripeStakerPoints == 45_00 * (_blk() - g0.lastUpdate)
    ua = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    lootbox.updateRipeRewards(sender=teller.address)
    bucket = ledger.ripeRewards().stakers
    alice_exp = _staker_loot(ua, ap, gp, bucket)
    assert bucket > 0
    assert alice_exp > 0
    alice_paid = teller.claimLoot(alice, False, sender=alice)
    clear_transient_storage()
    assert alice_paid == alice_exp
    bp2 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, bravo_token)
    gp2 = ledger.globalDepositPoints()
    ub2 = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, bravo_token)
    bucket2 = ledger.ripeRewards().stakers
    bob_exp = _staker_loot(ub2, bp2, gp2, bucket2)
    assert bucket2 > 0
    assert bob_exp > 0
    bob_paid = teller.claimLoot(bob, False, sender=bob)
    clear_transient_storage()
    assert bob_paid == bob_exp


def test_g8_f1_withdraw_to_zero_then_claim_keeps_enumerable(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    frozen = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    start, lb = frozen.lastUpdate, frozen.lastBalance
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    teller.withdraw(alpha_token, MAX_UINT256, alice, simple_erc20_vault, sender=alice)
    teller.claimLoot(alice, False, sender=alice)
    clear_transient_storage()
    asset, has_bal = simple_erc20_vault.getUserAssetAtIndexAndHasBalance(alice, 1)
    assert asset == alpha_token.address
    assert not has_bal
    assert ledger.numUserVaults(alice) > 1
    assert ledger.userVaults(alice, 1) == SIMPLE_VAULT_ID
    _enable(switchboard_alpha, governance)
    up, _, _ = lootbox.getLatestDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert up.balancePoints == lb * (_blk() - start)
    paid = teller.claimLoot(alice, False, sender=alice)
    clear_transient_storage()
    assert paid != 0


def test_g8_f1_delayed_post_reenable_mutations(
    launch_g8,
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    switchboard_alpha,
    switchboard_charlie,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    green_token,
    alice,
    bob,
    sally,
    charlie,
    alpha_token,
):
    launch_g8(_borrowersAlloc=10_00, _stakersAlloc=90_00)
    _credit_row(
        setAssetConfig,
        createDebtTerms,
        setGeneralDebtConfig,
        mock_price_source,
        alpha_token,
        _stakersPointsAlloc=15_00,
    )
    eve = boa.env.generate_address("g8-f1-eve")
    dave = boa.env.generate_address("g8-f1-dave")
    performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(bob, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(sally, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(eve, 500 * EIGHTEEN_DECIMALS, alpha_token)
    teller.borrow(50 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    a_dep = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    b_dep = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    s_dep = ledger.userDepositPoints(sally, SIMPLE_VAULT_ID, alpha_token)
    e_dep = ledger.userDepositPoints(eve, SIMPLE_VAULT_ID, alpha_token)
    a_bor = ledger.userBorrowPoints(alice)
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    performDeposit(alice, 10 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    performDeposit(charlie, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    teller.borrow(20 * EIGHTEEN_DECIMALS, charlie, False, sender=charlie)
    performDeposit(dave, 100 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    assert ledger.userDepositPoints(charlie, SIMPLE_VAULT_ID, alpha_token).lastUpdate == 0
    assert ledger.userBorrowPoints(charlie).lastUpdate == 0
    assert ledger.userDepositPoints(dave, SIMPLE_VAULT_ID, alpha_token).lastUpdate == 0
    _enable(switchboard_alpha, governance)
    boa.env.time_travel(blocks=50)

    teller.withdraw(alpha_token, MAX_UINT256, eve, simple_erc20_vault, sender=eve)
    e1 = ledger.userDepositPoints(eve, SIMPLE_VAULT_ID, alpha_token)
    assert e1.balancePoints == e_dep.lastBalance * (_blk() - e_dep.lastUpdate)
    assert e1.lastBalance == 0

    teller.withdraw(
        alpha_token, 100 * EIGHTEEN_DECIMALS, alice, simple_erc20_vault, sender=alice
    )
    a1 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert a1.balancePoints == a_dep.lastBalance * (_blk() - a_dep.lastUpdate)

    performDeposit(sally, 50 * EIGHTEEN_DECIMALS, alpha_token)
    clear_transient_storage()
    s1 = ledger.userDepositPoints(sally, SIMPLE_VAULT_ID, alpha_token)
    assert s1.balancePoints == s_dep.lastBalance * (_blk() - s_dep.lastUpdate)

    green_token.approve(teller.address, MAX_UINT256, sender=alice)
    teller.repay(10 * EIGHTEEN_DECIMALS, alice, False, False, sender=alice)
    _touch_bor(lootbox, teller, charlie)
    ab1 = ledger.userBorrowPoints(alice)
    cb1 = ledger.userBorrowPoints(charlie)
    assert ab1.points == a_bor.lastPrincipal * (_blk() - a_bor.lastUpdate)
    assert cb1.points == 0
    assert cb1.lastUpdate == _blk()
    assert ledger.globalBorrowPoints().points == ab1.points + cb1.points

    _touch_dep(lootbox, teller, dave, simple_erc20_vault, alpha_token)
    d1 = ledger.userDepositPoints(dave, SIMPLE_VAULT_ID, alpha_token)
    assert d1.balancePoints == 0
    assert d1.lastUpdate == _blk()
    _touch_dep(lootbox, teller, charlie, simple_erc20_vault, alpha_token)
    c1 = ledger.userDepositPoints(charlie, SIMPLE_VAULT_ID, alpha_token)
    assert c1.balancePoints == 0
    assert c1.lastUpdate == _blk()

    switchboard_charlie.updateDepositPoints(
        bob, SIMPLE_VAULT_ID, alpha_token, sender=governance.address
    )
    b2 = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    assert b2.balancePoints == b_dep.lastBalance * (_blk() - b_dep.lastUpdate)


def test_g8_f1_ripegov_releaselock_uses_frozen_normalized_share(
    launch_g8,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    ripe_gov_vault,
    ripe_token,
    whale,
    alice,
    sally,
):
    launch_g8()
    for user, amt in ((sally, 100 * EIGHTEEN_DECIMALS), (alice, 1000 * EIGHTEEN_DECIMALS)):
        ripe_token.transfer(user, amt, sender=whale)
        ripe_token.approve(teller, amt, sender=user)
        teller.depositIntoGovVault(ripe_token, amt, DAY_IN_BLOCKS, user, sender=user)
        clear_transient_storage()
    frozen = ledger.userDepositPoints(alice, GOV_VAULT_ID, ripe_token)
    start, lb = frozen.lastUpdate, frozen.lastBalance
    assert lb != 0
    boa.env.time_travel(blocks=20)
    before = _dep_snap(ledger, alice, ripe_token, GOV_VAULT_ID)
    _disable(switchboard_alpha, governance)
    teller.releaseLock(ripe_token, alice, sender=alice)
    clear_transient_storage()
    _assert_dep_frozen(before, _dep_snap(ledger, alice, ripe_token, GOV_VAULT_ID))
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, ripe_gov_vault, ripe_token, GOV_VAULT_ID)
    after = ledger.userDepositPoints(alice, GOV_VAULT_ID, ripe_token)
    assert after.balancePoints == lb * (_blk() - start)


def test_g8_f1_f2_charlie_pays_stored_then_can_claim_reverts(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    switchboard_charlie,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
    ripe_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    boa.env.time_travel(blocks=30)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    stored = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert stored.balancePoints != 0
    start, lb = stored.lastUpdate, stored.lastBalance
    _disable(switchboard_alpha, governance)
    owed = lootbox.getClaimableLoot(alice)
    paid = switchboard_charlie.claimDepositLootForAsset(
        alice, SIMPLE_VAULT_ID, alpha_token, sender=governance.address
    )
    clear_transient_storage()
    assert paid == owed
    assert paid != 0
    after = _dep_snap(ledger, alice, alpha_token)
    assert after[0].lastUpdate == start
    assert after[0].lastBalance == lb
    switchboard_alpha.setCanClaimLoot(False, sender=governance.address)
    clocks = _dep_snap(ledger, alice, alpha_token)
    pre_supply = ripe_token.totalSupply()
    pre_avail = ledger.ripeAvailForRewards()
    with pytest.raises(BoaError) as e:
        switchboard_charlie.claimDepositLootForAsset(
            alice, SIMPLE_VAULT_ID, alpha_token, sender=governance.address
        )
    assert has_dev_reason(e.value, "loot claims disabled")
    _assert_dep_frozen(clocks, _dep_snap(ledger, alice, alpha_token))
    assert ripe_token.totalSupply() == pre_supply
    assert ledger.ripeAvailForRewards() == pre_avail


def test_g8_f1_exited_holder_keeps_asset_weight_until_touched(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    bob,
    alpha_token,
):
    """Two equal holders, one exits while frozen: remaining holder is 50% until both are touched."""
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token)
    a0 = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    b0 = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    assert a0.lastBalance == b0.lastBalance != 0
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    teller.withdraw(alpha_token, MAX_UINT256, alice, simple_erc20_vault, sender=alice)
    assert ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token).lastBalance == a0.lastBalance
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, bob, simple_erc20_vault, alpha_token)
    bob_pts = ledger.userDepositPoints(bob, SIMPLE_VAULT_ID, alpha_token)
    ap = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    span = _blk() - b0.lastUpdate
    assert bob_pts.balancePoints == b0.lastBalance * span
    assert ap.balancePoints == (a0.lastBalance + b0.lastBalance) * span
    assert bob_pts.balancePoints * 2 == ap.balancePoints
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    alice_pts = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    ap2 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    assert alice_pts.balancePoints == a0.lastBalance * (_blk() - a0.lastUpdate)
    assert alice_pts.lastBalance == 0
    assert ap2.balancePoints == alice_pts.balancePoints + bob_pts.balancePoints


def test_g8_f1_asset_alloc_change_during_freeze_prices_whole_span(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token, _stakersPointsAlloc=15_00)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    a0 = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    _staker_row(setAssetConfig, alpha_token, _stakersPointsAlloc=30_00)
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    ap = ledger.assetDepositPoints(SIMPLE_VAULT_ID, alpha_token)
    assert ap.ripeStakerPoints == 30_00 * (_blk() - a0.lastUpdate)


def test_g8_f1_reset_after_reenable_clears_span_credit(
    launch_g8,
    setAssetConfig,
    performDeposit,
    switchboard_alpha,
    switchboard_delta,
    governance,
    lootbox,
    teller,
    ledger,
    simple_erc20_vault,
    alice,
    alpha_token,
):
    launch_g8()
    _staker_row(setAssetConfig, alpha_token)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    start = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token).lastUpdate
    lb = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token).lastBalance
    boa.env.time_travel(blocks=20)
    _disable(switchboard_alpha, governance)
    lootbox.resetUserBalancePoints(
        alice, alpha_token, SIMPLE_VAULT_ID, sender=switchboard_delta.address
    )
    assert ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token).balancePoints == 0
    _enable(switchboard_alpha, governance)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    credited = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert credited.balancePoints == lb * (_blk() - start)
    lootbox.resetUserBalancePoints(
        alice, alpha_token, SIMPLE_VAULT_ID, sender=switchboard_delta.address
    )
    assert ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token).balancePoints == 0
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    after = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert after.balancePoints == 0
    boa.env.time_travel(blocks=5)
    _touch_dep(lootbox, teller, alice, simple_erc20_vault, alpha_token)
    replayed = ledger.userDepositPoints(alice, SIMPLE_VAULT_ID, alpha_token)
    assert replayed.balancePoints == after.lastBalance * 5


def test_g8_f2_claim_borrow_loot_ignores_can_claim_loot(
    launch_g8,
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    switchboard_alpha,
    governance,
    lootbox,
    teller,
    ledger,
    alice,
    alpha_token,
    ripe_token,
):
    """L2 leftover on rh: claimBorrowLoot stays ungated beside the gated deposit sibling."""
    launch_g8(_borrowersAlloc=100_00, _stakersAlloc=0)
    _credit_row(
        setAssetConfig,
        createDebtTerms,
        setGeneralDebtConfig,
        mock_price_source,
        alpha_token,
    )
    performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token)
    teller.borrow(50 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    boa.env.time_travel(blocks=30)
    _touch_bor(lootbox, teller, alice)
    assert ledger.userBorrowPoints(alice).points != 0
    switchboard_alpha.setCanClaimLoot(False, sender=governance.address)
    pre_supply = ripe_token.totalSupply()
    paid = lootbox.claimBorrowLoot(alice, sender=teller.address)
    clear_transient_storage()
    assert paid != 0
    assert ripe_token.totalSupply() - pre_supply == paid
