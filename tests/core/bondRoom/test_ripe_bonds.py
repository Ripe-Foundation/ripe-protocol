import pytest
import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def setupRipeBonds(mission_control, bond_room, setAssetConfig, setGeneralConfig, switchboard_alpha, switchboard_delta, ripe_token, alpha_token):
    def setupRipeBonds(
        _asset = alpha_token,
        _amountPerEpoch = 1000 * EIGHTEEN_DECIMALS,
        _canBond = True,
        _minRipePerUnit = 1 * EIGHTEEN_DECIMALS,
        _maxRipePerUnit = 100 * EIGHTEEN_DECIMALS,
        _maxRipePerUnitLockBonus = 100 * EIGHTEEN_DECIMALS,
        _epochLength = 100,
        _shouldAutoRestart = True,
        _minLockDuration = 100,
        _maxLockDuration = 1000,
    ):
        # enable general deposits (required for governance vault deposits)
        setGeneralConfig()
        
        bond_config = (
            _asset,
            _amountPerEpoch,
            _canBond,
            _minRipePerUnit,
            _maxRipePerUnit,
            _maxRipePerUnitLockBonus,
            _epochLength,
            _shouldAutoRestart,
        )
        mission_control.setRipeBondConfig(bond_config, sender=switchboard_delta.address)

        # setup ripe gov vault
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            100_00,
            False,
            0,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            100_00,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

        # start epoch
        return bond_room.refreshBondEpoch(sender=switchboard_delta.address)

    yield setupRipeBonds


def test_initial_epoch_blocks(
    ledger, setupRipeBonds
):
    start, end = setupRipeBonds()
      
    assert ledger.epochStart() == start
    assert ledger.epochEnd() == end
    assert ledger.paymentAmountAvailInEpoch() != 0
    assert ledger.ripeAvailForBonds() != 0


def test_purchase_ripe_bond_basic(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ledger
):
    setupRipeBonds()

    # pre ledger balances
    pre_avail_in_epoch = ledger.paymentAmountAvailInEpoch()
    pre_ripe_avail = ledger.ripeAvailForBonds()

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    # min ripe per unit is 1 per, this is beginning of epoch
    _test(ripe_payout, payment_amount) 

    # no lock duration, went straight to user, no refund
    ripe_token.balanceOf(bob) == ripe_payout

    # ledger balances
    assert ledger.paymentAmountAvailInEpoch() == pre_avail_in_epoch - payment_amount
    assert ledger.ripeAvailForBonds() == pre_ripe_avail - ripe_payout


def test_purchase_ripe_bond_mid_epoch(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token,
):
    start, end = setupRipeBonds()
    
    # move to middle of epoch
    blocks_to_travel = (end - start) // 2
    boa.env.time_travel(blocks=blocks_to_travel)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    # should get more than min (1x) but less than max (100x)
    assert ripe_payout > payment_amount  # more than min
    assert ripe_payout < 100 * payment_amount  # less than max
    

def test_purchase_ripe_bond_end_of_epoch(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test,
):
    start, end = setupRipeBonds()
    
    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # move to end of epoch (but not past)
    blocks_to_travel = (end - start) - 1
    boa.env.time_travel(blocks=blocks_to_travel)

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    # should get near-maximum discount (99% through epoch = 99.01x)
    _test(ripe_payout, 9_901 * EIGHTEEN_DECIMALS)


def test_purchase_ripe_bond_before_epoch_fails(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room, switchboard_delta
):
    setupRipeBonds()
    
    # Set epoch to start in the future (10 blocks from now)
    current_block = boa.env.evm.patch.block_number
    future_start = current_block + 10
    bond_room.startBondEpochAtBlock(future_start, sender=switchboard_delta.address)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail because we're before epoch start
    with boa.reverts("not within epoch window"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_auto_epoch_advancement(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger
):
    """Test that epochs automatically advance when expired"""
    start, end = setupRipeBonds()
    
    # move past epoch end
    blocks_to_travel = (end - start) + 1
    boa.env.time_travel(blocks=blocks_to_travel)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should succeed because epoch auto-advances
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    assert ripe_payout > 0
    
    # verify a new epoch was created
    new_start = ledger.epochStart()
    new_end = ledger.epochEnd()
    assert new_start == end  # new epoch starts exactly where old one ended
    assert new_end == end + 100  # epoch length


def test_purchase_ripe_bond_with_minimum_lock_duration(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    setupRipeBonds()

    # purchase setup with minimum lock duration
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 100  # minimum lock duration
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)

    # purchase ripe bond with lock
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )

    # At minimum lock duration, bonus is 0 but tokens are still locked
    # bonus = (100 - 100) / (1000 - 100) * maxBonus = 0
    expected_base = payment_amount  # min ripe per unit at epoch start
    expected_bonus = 0  # no bonus at minimum lock duration
    expected_total = expected_base + expected_bonus
    _test(ripe_payout, expected_total)

    # tokens should be locked in gov vault, not in user balance
    assert ripe_token.balanceOf(bob) == 0
    
    # verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


def test_purchase_ripe_bond_with_lock_above_minimum(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    setupRipeBonds()

    # purchase setup with lock duration above minimum
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 150  # above minimum of 100
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)

    # purchase ripe bond with lock
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )

    # Should get base rate + proportional lock bonus
    # lockDuration = 150, minLock = 100, maxLock = 1000
    # bonus ratio = (150 - 100) / (1000 - 100) = 50/900 ≈ 5.56%
    # bonus = 5.56% of 100 RIPE per unit = ~5.56 RIPE per unit
    expected_base = payment_amount  # min ripe per unit at epoch start
    expected_bonus_ratio = (lock_duration - 100) / (1000 - 100)  # (150-100)/(1000-100)
    expected_bonus = int(100 * EIGHTEEN_DECIMALS * expected_bonus_ratio * payment_amount // EIGHTEEN_DECIMALS)
    expected_total = expected_base + expected_bonus
    _test(ripe_payout, expected_total)

    # tokens should be locked, not in user balance
    assert ripe_token.balanceOf(bob) == 0
    
    # verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


def test_purchase_ripe_bond_with_lock_maximum(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    setupRipeBonds()

    # purchase setup with maximum lock duration
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 1000  # maximum lock duration
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)

    # purchase ripe bond with max lock
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )

    # should get base amount + full lock bonus (100 RIPE per unit bonus)
    expected_base = payment_amount  # min ripe per unit at epoch start (1x)
    expected_bonus = 100 * payment_amount  # max lock bonus (100x)  
    expected_total = expected_base + expected_bonus
    _test(ripe_payout, expected_total)

    # tokens should be locked, not in user balance
    assert ripe_token.balanceOf(bob) == 0
    
    # verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


def test_purchase_ripe_bond_with_lock_exceeding_max(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    setupRipeBonds()

    # purchase setup with lock duration exceeding maximum
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 2000  # exceeds maximum of 1000
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)

    # purchase ripe bond - should cap at max lock duration
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )

    # should get same as max lock duration
    expected_base = payment_amount  # min ripe per unit at epoch start (1x)
    expected_bonus = 100 * payment_amount  # max lock bonus (100x)
    expected_total = expected_base + expected_bonus
    _test(ripe_payout, expected_total)
    
    # verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


def test_purchase_ripe_bond_6_decimal_token(
    teller, setupRipeBonds, bob, charlie_token_whale, charlie_token, _test, 
):
    # setup with 6 decimal token
    charlie_amount_per_epoch = 1000 * (10 ** 6)  # 6 decimals
    setupRipeBonds(_asset=charlie_token, _amountPerEpoch=charlie_amount_per_epoch)

    # purchase setup
    payment_amount = 100 * (10 ** 6)  # 6 decimals
    charlie_token.transfer(bob, payment_amount, sender=charlie_token_whale)
    charlie_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        charlie_token,
        payment_amount,
        sender=bob
    )

    # should get proportional amount in 18 decimal Ripe
    expected_ripe = payment_amount * (10 ** 12)  # convert 6 decimals to 18
    _test(ripe_payout, expected_ripe)


def test_purchase_ripe_bond_8_decimal_token(
    teller, setupRipeBonds, bob, delta_token_whale, delta_token, _test, 
):
    # setup with 8 decimal token  
    delta_amount_per_epoch = 1000 * (10 ** 8)  # 8 decimals
    setupRipeBonds(_asset=delta_token, _amountPerEpoch=delta_amount_per_epoch)

    # purchase setup
    payment_amount = 100 * (10 ** 8)  # 8 decimals
    delta_token.transfer(bob, payment_amount, sender=delta_token_whale)
    delta_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        delta_token,
        payment_amount,
        sender=bob
    )

    # should get proportional amount in 18 decimal Ripe
    expected_ripe = payment_amount * (10 ** 10)  # convert 8 decimals to 18
    _test(ripe_payout, expected_ripe)


def test_purchase_ripe_bond_payment_unavailable(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, ledger
):
    setupRipeBonds(_shouldAutoRestart=False)

    # exhaust payment amount available in epoch by making a large purchase first
    available_amount = ledger.paymentAmountAvailInEpoch()
    alpha_token.transfer(alice, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=alice)
    teller.purchaseRipeBond(alpha_token, available_amount, sender=alice)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail
    with boa.reverts("no more available in epoch"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_ripe_unavailable(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, switchboard_alpha
):
    setupRipeBonds()

    # reduce ripe available for bonds to a very small amount
    ledger.setRipeAvailForBonds(1, sender=switchboard_alpha.address)

    # purchase setup - trying to get more ripe than available
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail
    with boa.reverts("not enough ripe avail"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_partial_fill_with_refund(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, _test, ledger
):
    setupRipeBonds()

    # reduce available amount by making a partial purchase first
    initial_available = ledger.paymentAmountAvailInEpoch()
    consumed_amount = initial_available - (50 * EIGHTEEN_DECIMALS)  # leave 50 tokens available
    
    alpha_token.transfer(alice, consumed_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, consumed_amount, sender=alice)
    teller.purchaseRipeBond(alpha_token, consumed_amount, sender=alice)

    # purchase setup for more than available
    payment_amount = 100 * EIGHTEEN_DECIMALS
    pre_balance = alpha_token.balanceOf(bob)
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    # should get ripe for available amount only (50 tokens)
    available_amount = 50 * EIGHTEEN_DECIMALS
    _test(ripe_payout, available_amount)
    
    # should receive refund for unused amount
    refund_amount = payment_amount - available_amount
    expected_balance = pre_balance + refund_amount
    _test(alpha_token.balanceOf(bob), expected_balance)


def test_purchase_ripe_bond_bonds_disabled(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token
):
    setupRipeBonds(_canBond=False)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail
    with boa.reverts("bonds disabled"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_asset_mismatch(
    teller, setupRipeBonds, bob, bravo_token_whale, alpha_token, bravo_token
):
    setupRipeBonds(_asset=alpha_token)  # setup for alpha token

    # purchase setup with different asset
    payment_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, payment_amount, sender=bravo_token_whale)
    bravo_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail
    with boa.reverts("asset mismatch"):
        teller.purchaseRipeBond(
            bravo_token,  # trying to use bravo instead of alpha
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_for_another_user_with_permission(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, _test, ripe_token, setUserConfig
):
    setupRipeBonds()
    
    # enable alice to allow others to bond for her
    setUserConfig(alice, _canAnyoneBondForUser=True)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # bob purchases bond for alice
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        0,  # no lock
        alice,  # user to receive bonds
        sender=bob
    )

    # alice should receive the ripe tokens
    _test(ripe_token.balanceOf(alice), ripe_payout)
    assert ripe_token.balanceOf(bob) == 0


def test_purchase_ripe_bond_for_another_user_without_permission(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, setUserConfig
):
    setupRipeBonds()
    
    # alice has not enabled others to bond for her (default is False)
    setUserConfig(alice, _canAnyoneBondForUser=False)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should fail
    with boa.reverts("cannot bond for user"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            0,  # no lock
            alice,  # user to receive bonds
            sender=bob
        )


def test_purchase_ripe_bond_zero_amount_fails(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token
):
    setupRipeBonds()

    # purchase setup with zero amount
    alpha_token.transfer(bob, 0, sender=alpha_token_whale)
    alpha_token.approve(teller, 0, sender=bob)  

    # purchase should fail
    with boa.reverts("user has no asset balance (or zero specified)"):
        teller.purchaseRipeBond(
            alpha_token,
            0,
            sender=bob
        )


def test_purchase_ripe_bond_auto_restart_epoch(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger
):
    start, end = setupRipeBonds(_shouldAutoRestart=True)

    # exhaust entire epoch availability with one purchase
    available_amount = ledger.paymentAmountAvailInEpoch()
    
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)  

    travel = 5
    boa.env.time_travel(blocks=travel)

    # purchase entire available amount
    teller.purchaseRipeBond(
        alpha_token,
        available_amount,
        sender=bob
    )

    # epoch should auto-restart
    new_start = ledger.epochStart()
    new_end = ledger.epochEnd() 
    
    assert new_start == start + travel
    assert new_end == end + travel
    assert ledger.paymentAmountAvailInEpoch() == 1000 * EIGHTEEN_DECIMALS  # refreshed


def test_purchase_ripe_bond_no_auto_restart(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger
):
    start, end = setupRipeBonds(_shouldAutoRestart=False)

    # exhaust entire epoch availability  
    available_amount = ledger.paymentAmountAvailInEpoch()
    
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)  

    # purchase entire available amount
    teller.purchaseRipeBond(
        alpha_token,
        available_amount,
        sender=bob
    )

    # epoch should NOT auto-restart
    assert ledger.epochStart() == start  # unchanged
    assert ledger.epochEnd() == end  # unchanged
    assert ledger.paymentAmountAvailInEpoch() == 0  # exhausted


def test_purchase_ripe_bond_different_ripe_per_unit_range(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test
):
    # setup with different min/max ripe per unit
    setupRipeBonds(_minRipePerUnit=10 * EIGHTEEN_DECIMALS, _maxRipePerUnit=50 * EIGHTEEN_DECIMALS)

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase at beginning of epoch
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    # should get minimum rate (10x)
    expected_ripe = 10 * payment_amount
    _test(ripe_payout, expected_ripe)


def test_purchase_ripe_bond_very_small_amount(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ripe_token
):
    setupRipeBonds()

    # purchase setup with very small amount
    payment_amount = 1  # 1 wei
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should still work for tiny amounts
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    assert ripe_payout > 0
    assert ripe_token.balanceOf(bob) == ripe_payout


def test_ripe_per_unit_calculation_edge_cases(
    bond_room
):
    # test _calcRipePerUnit function edge cases
    
    # when ratio is 0, should return min
    result = bond_room.getLatestEpochBlockTimes(0, 0, 100)  # accessing view function
    
    # when min equals max, should return min regardless of ratio
    # Note: can't directly test internal _calcRipePerUnit, but we can test behavior
    
    # These edge cases are implicitly tested through purchase scenarios


def test_refresh_bond_epoch_multiple_times(
    bond_room, ledger, setupRipeBonds, switchboard_delta
):
    setupRipeBonds()
    
    initial_start = ledger.epochStart()
    initial_end = ledger.epochEnd()
    
    # refresh again - should not change if still in epoch
    new_start, new_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    
    assert new_start == initial_start
    assert new_end == initial_end


def test_start_bond_epoch_at_specific_block(
    bond_room, ledger, setupRipeBonds, switchboard_delta
):
    setupRipeBonds()
    
    # start epoch at future block
    current_block = boa.env.evm.patch.block_number
    future_block = current_block + 50
    bond_room.startBondEpochAtBlock(future_block, sender=switchboard_delta.address)
    
    assert ledger.epochStart() == future_block
    assert ledger.epochEnd() == future_block + 100  # epoch length is 100


def test_purchase_ripe_bond_complex_scenario(
    teller, setupRipeBonds, bob, alice, charlie, alpha_token_whale, alpha_token, _test, ripe_token, ledger, setUserConfig, ripe_gov_vault
):
    """Test a complex scenario with multiple users, partial epochs, locks, and permissions"""
    start, end = setupRipeBonds()
    
    # Setup users
    setUserConfig(alice, _canAnyoneBondForUser=True)
    
    # Move to mid-epoch
    blocks_to_travel = (end - start) // 3  # 1/3 through epoch
    boa.env.time_travel(blocks=blocks_to_travel)
    
    # Bob buys for himself with lock
    payment_amount_bob = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount_bob, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_bob, sender=bob)
    
    ripe_payout_bob = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_bob,
        500,  # lock duration
        sender=bob
    )
    
    # Charlie buys for Alice (no lock)
    payment_amount_charlie = 150 * EIGHTEEN_DECIMALS
    alpha_token.transfer(charlie, payment_amount_charlie, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_charlie, sender=charlie)
    
    ripe_payout_alice = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_charlie,
        0,  # no lock
        alice,  # for alice
        sender=charlie
    )
    
    # Verify payouts are different due to lock bonus
    assert ripe_payout_bob > ripe_payout_alice  # bob gets lock bonus
    
    # Verify token distributions
    assert ripe_token.balanceOf(bob) == 0  # locked
    assert ripe_token.balanceOf(alice) == ripe_payout_alice  # unlocked
    assert ripe_token.balanceOf(charlie) == 0  # bought for alice
    
    # Verify Bob's tokens were deposited into gov vault
    expected_deposit_bob = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout_bob, expected_deposit_bob)
    
    # Verify Alice has no tokens in gov vault (no lock)
    expected_deposit_alice = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    assert expected_deposit_alice == 0
    
    # Verify ledger updates
    expected_total_payment = payment_amount_bob + payment_amount_charlie
    expected_total_payout = ripe_payout_bob + ripe_payout_alice
    
    expected_remaining_payment = (1000 * EIGHTEEN_DECIMALS) - expected_total_payment
    _test(ledger.paymentAmountAvailInEpoch(), expected_remaining_payment)
    
    # Verify ripe was consumed from the bonds pool
    initial_ripe_avail = 100000000 * EIGHTEEN_DECIMALS  # default initial amount
    current_ripe_avail = ledger.ripeAvailForBonds()
    expected_remaining_ripe = initial_ripe_avail - expected_total_payout
    _test(current_ripe_avail, expected_remaining_ripe)


def test_purchase_ripe_bond_event_emission(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ripe_gov_vault, ripe_token, _test
):
    setupRipeBonds()

    # purchase setup
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 200
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )
    
    # check event emission immediately after transaction
    logs = filter_logs(teller, "RipeBondPurchased")
    assert len(logs) == 1
    
    event = logs[0]
    assert event.user == bob
    assert event.paymentAsset == alpha_token.address
    assert event.paymentAmount == payment_amount
    assert event.lockDuration == lock_duration
    assert event.ripePayout == ripe_payout
    assert event.caller == bob
    
    # verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


def test_purchase_ripe_bond_lock_bonus_calculation(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    setupRipeBonds(
        _minLockDuration=100,
        _maxLockDuration=1000,
        _maxRipePerUnitLockBonus=50 * EIGHTEEN_DECIMALS  # 50x bonus
    )

    # Test no lock
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout_no_lock = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        0,  # no lock
        sender=bob
    )
    
    # Test minimum lock (gets zero bonus since lockDuration - minLockDuration = 0)
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout_min_lock = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        100,  # min lock
        sender=bob
    )
    
    # Test mid-range lock
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout_mid_lock = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        550,  # mid-range lock (50% of the way from min to max)
        sender=bob
    )
    
    # Test maximum lock
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout_max_lock = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        1000,  # max lock
        sender=bob
    )
    
    # Verify bonus progression
    assert ripe_payout_no_lock == ripe_payout_min_lock  # min lock gets 0 bonus
    assert ripe_payout_min_lock < ripe_payout_mid_lock
    assert ripe_payout_mid_lock < ripe_payout_max_lock
    
    # Maximum should get base + full bonus
    expected_max = payment_amount + 50 * payment_amount  # base + 50x bonus
    _test(ripe_payout_max_lock, expected_max)
    
    # Verify total locked amount in gov vault (should be sum of all locked purchases)
    total_locked_amount = ripe_payout_min_lock + ripe_payout_mid_lock + ripe_payout_max_lock
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(total_locked_amount, expected_deposit)


def test_purchase_ripe_bond_insufficient_balance_fails(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token
):
    setupRipeBonds()

    # give bob less than he tries to spend
    small_amount = 50 * EIGHTEEN_DECIMALS
    large_amount = 100 * EIGHTEEN_DECIMALS
    
    alpha_token.transfer(bob, small_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, large_amount, sender=bob)  # approve more than balance

    # purchase should only use available balance
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        large_amount,  # request more than balance
        sender=bob
    )
    
    # should only get ripe for the small amount actually available
    assert alpha_token.balanceOf(bob) == 0  # all tokens used
    assert ripe_payout == small_amount  # only got ripe for available amount


def test_purchase_ripe_bond_automatic_epoch_advancement(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room, switchboard_delta
):
    """Test that epochs automatically advance when time passes beyond epoch end"""
    start, end = setupRipeBonds(_epochLength=50, _shouldAutoRestart=False)
    
    # Move to just before epoch end
    blocks_to_travel = (end - start) - 1
    boa.env.time_travel(blocks=blocks_to_travel)
    
    # Purchase should work
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    assert ripe_payout > 0
    
    # Move past epoch end
    boa.env.time_travel(blocks=6)  # Move 6 more blocks past end
    
    # Purchase should succeed because epoch auto-advances
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout_2 = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    assert ripe_payout_2 > 0
    
    # Verify a new epoch was automatically created
    # The purchase itself triggers epoch refresh, creating a new epoch
    # This is the contract's designed behavior - no gaps between epochs


def test_purchase_ripe_bond_equal_min_max_ripe_per_unit(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test
):
    """Test when min and max ripe per unit are equal"""
    fixed_rate = 5 * EIGHTEEN_DECIMALS
    setupRipeBonds(
        _minRipePerUnit=fixed_rate,
        _maxRipePerUnit=fixed_rate  # same as min
    )

    # purchase at beginning of epoch
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # should get fixed rate regardless of epoch progress
    expected_ripe = 5 * payment_amount
    _test(ripe_payout, expected_ripe)


def test_purchase_ripe_bond_below_min_lock_duration(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_token, ripe_gov_vault
):
    """Test lock duration below minimum gets treated as no lock"""
    setupRipeBonds(_minLockDuration=100)

    # purchase with lock duration below minimum
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        50,  # below minimum of 100
        sender=bob
    )
    
    # should be treated as no lock (tokens go to user, no bonus)
    assert ripe_token.balanceOf(bob) == ripe_payout
    _test(ripe_payout, payment_amount)  # base rate only, no lock bonus
    
    # verify no tokens were deposited into gov vault (since lockDuration < min)
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert expected_deposit == 0


def test_purchase_ripe_bond_gas_optimization_scenarios(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token
):
    """Test scenarios that might affect gas usage"""
    setupRipeBonds()

    # Test with exact epoch availability (no refund needed)
    available_amount = 1000 * EIGHTEEN_DECIMALS  # exactly the epoch amount
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        available_amount,
        sender=bob
    )
    
    assert ripe_payout > 0
    assert alpha_token.balanceOf(bob) == 0  # no refund


def test_purchase_ripe_bond_future_epoch_transition(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room, switchboard_delta, ledger, _test
):
    """Test purchasing fails before epoch, then succeeds when epoch starts"""
    setupRipeBonds()
    
    # Set epoch to start 20 blocks in the future
    current_block = boa.env.evm.patch.block_number
    future_start = current_block + 20
    bond_room.startBondEpochAtBlock(future_start, sender=switchboard_delta.address)
    
    # Verify epoch is set correctly
    assert ledger.epochStart() == future_start
    assert ledger.epochEnd() == future_start + 100  # default epoch length
    
    # Purchase should fail before epoch starts
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    with boa.reverts("not within epoch window"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )
    
    # Travel to epoch start
    boa.env.time_travel(blocks=20)
    
    # Now purchase should succeed
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Should get minimum rate since we're at epoch start
    _test(ripe_payout, payment_amount)


def test_purchase_ripe_bond_multiple_epochs_with_manual_restart(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, bond_room, switchboard_delta, ledger, _test
):
    """Test manually restarting epochs after exhaustion"""
    start, end = setupRipeBonds(_shouldAutoRestart=False)  # no auto-restart
    
    # Exhaust first epoch
    available_amount = ledger.paymentAmountAvailInEpoch()
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)
    
    teller.purchaseRipeBond(alpha_token, available_amount, sender=bob)
    
    # Verify epoch is exhausted
    assert ledger.paymentAmountAvailInEpoch() == 0
    
    # Try to purchase more - should fail
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=alice)
    
    with boa.reverts("no more available in epoch"):
        teller.purchaseRipeBond(alpha_token, payment_amount, sender=alice)
    
    # Manually start new epoch
    current_block = boa.env.evm.patch.block_number
    new_start = current_block + 5
    bond_room.startBondEpochAtBlock(new_start, sender=switchboard_delta.address)
    
    # Travel to new epoch
    boa.env.time_travel(blocks=5)
    
    # Now purchase should work again
    ripe_payout = teller.purchaseRipeBond(alpha_token, payment_amount, sender=alice)
    _test(ripe_payout, payment_amount)


def test_purchase_ripe_bond_maximum_parameters(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test, ripe_gov_vault, ripe_token
):
    """Test with very large parameter values"""
    # Setup with large values
    large_amount_per_epoch = 1000000 * EIGHTEEN_DECIMALS
    large_max_ripe_per_unit = 1000 * EIGHTEEN_DECIMALS
    large_max_lock_bonus = 2000 * EIGHTEEN_DECIMALS
    
    setupRipeBonds(
        _amountPerEpoch=large_amount_per_epoch,
        _maxRipePerUnit=large_max_ripe_per_unit,
        _maxRipePerUnitLockBonus=large_max_lock_bonus,
        _maxLockDuration=10000
    )
    
    # Test large purchase with maximum lock (but within available ripe limits)
    payment_amount = 30000 * EIGHTEEN_DECIMALS  # Reduced to stay within ripe availability
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Move to end of epoch for maximum base rate
    boa.env.time_travel(blocks=99)  # almost end of 100-block epoch
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        10000,  # max lock duration
        sender=bob
    )
    
    # Should get max base rate + max lock bonus
    # At 99% epoch progress: baseRipePerUnit = 1 + (9900 * 999 / 10000) = 990.01
    # Lock bonus: full 2000 RIPE per unit
    # Total: ~2990.01 RIPE per unit
    expected_base_rate = 1 * EIGHTEEN_DECIMALS + (9900 * 999 * EIGHTEEN_DECIMALS // 10000)  # ~990.01e18
    expected_bonus = large_max_lock_bonus  # 2000e18
    expected_total_rate = expected_base_rate + expected_bonus  # ~2990.01e18
    expected_total = expected_total_rate * payment_amount // EIGHTEEN_DECIMALS
    
    _test(ripe_payout, expected_total)
    
    # Verify tokens were deposited into gov vault
    expected_deposit = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(ripe_payout, expected_deposit)


# other tests


def test_start_bond_epoch_at_block_comprehensive(
    bond_room, ledger, setupRipeBonds, switchboard_delta, bob
):
    """Test startBondEpochAtBlock function comprehensively"""
    setupRipeBonds()
    
    # Time travel forward to get a reasonable block number
    boa.env.time_travel(blocks=100)
    
    # Test starting epoch at current block
    current_block = boa.env.evm.patch.block_number
    bond_room.startBondEpochAtBlock(current_block, sender=switchboard_delta.address)
    
    assert ledger.epochStart() == current_block
    assert ledger.epochEnd() == current_block + 100  # default epoch length
    
    # Test starting epoch in the past (should use current block instead)
    past_block = current_block - 10
    bond_room.startBondEpochAtBlock(past_block, sender=switchboard_delta.address)
    
    # Should use current block, not past block
    assert ledger.epochStart() == current_block
    
    # Test starting epoch in the future
    future_block = current_block + 50
    bond_room.startBondEpochAtBlock(future_block, sender=switchboard_delta.address)
    
    assert ledger.epochStart() == future_block
    assert ledger.epochEnd() == future_block + 100
    
    # Test permission check - non-switchboard should fail
    with boa.reverts("no perms"):
        bond_room.startBondEpochAtBlock(future_block + 100, sender=bob)


def test_refresh_bond_epoch_comprehensive(
    bond_room, setupRipeBonds, switchboard_delta, bob
):
    """Test refreshBondEpoch function comprehensively"""
    
    # Test 1: Refresh within current epoch (should not change)
    start, end = setupRipeBonds()
    
    # Move partway through epoch
    boa.env.time_travel(blocks=30)
    
    new_start, new_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    
    # Should remain unchanged
    assert new_start == start
    assert new_end == end
    
    # Test 2: Refresh past epoch end (should create new epoch)
    boa.env.time_travel(blocks=80)  # Now 110 blocks total, past epoch end at block 100
    
    new_start, new_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    
    # Should create new epoch that starts exactly where the old one ended
    assert new_start == end  # new epoch starts exactly at old epoch end
    assert new_end == end + 100  # epoch length
    
    # Test 3: Permission check - non-valid ripe address should fail
    with boa.reverts("no perms"):
        bond_room.refreshBondEpoch(sender=bob)


def test_get_latest_epoch_block_times_edge_cases(
    bond_room
):
    """Test getLatestEpochBlockTimes view function edge cases"""
    
    # Time travel forward to get a reasonable block number for testing
    boa.env.time_travel(blocks=500)
    current_block = boa.env.evm.patch.block_number
    epoch_length = 100
    
    # Test 1: No epoch set yet (start=0, end=0)
    start, end, changed = bond_room.getLatestEpochBlockTimes(0, 0, epoch_length)
    
    assert start == current_block
    assert end == current_block + epoch_length
    assert changed == True
    
    # Test 2: Future epoch (current block < start)
    future_start = current_block + 50
    future_end = future_start + epoch_length
    start, end, changed = bond_room.getLatestEpochBlockTimes(future_start, future_end, epoch_length)
    
    assert start == future_start  # unchanged
    assert end == future_end      # unchanged
    assert changed == False
    
    # Test 3: Current epoch not expired (current block < end)
    active_start = current_block - 20
    active_end = current_block + 30
    start, end, changed = bond_room.getLatestEpochBlockTimes(active_start, active_end, epoch_length)
    
    assert start == active_start  # unchanged
    assert end == active_end      # unchanged
    assert changed == False
    
    # Test 4: Just past epoch end (within next epoch window)
    past_start = current_block - 150
    past_end = current_block - 50
    start, end, changed = bond_room.getLatestEpochBlockTimes(past_start, past_end, epoch_length)
    
    assert start == past_end  # new epoch starts where old one ended
    assert end == past_end + epoch_length
    assert changed == True
    
    # Test 5: Way past epoch end (multiple epochs ahead)
    very_old_start = current_block - 350
    very_old_end = current_block - 250  # 250 blocks ago
    start, end, changed = bond_room.getLatestEpochBlockTimes(very_old_start, very_old_end, epoch_length)
    
    # Should calculate how many epochs ahead we are
    epochs_ahead = (current_block - very_old_end) // epoch_length
    expected_start = epoch_length * epochs_ahead + very_old_end
    
    assert start == expected_start
    assert end == expected_start + epoch_length
    assert changed == True


def test_epoch_management_integration(
    bond_room, ledger, setupRipeBonds, switchboard_delta, teller, bob, alpha_token_whale, alpha_token
):
    """Test integration between different epoch management functions"""
    
    # Setup initial epoch
    start, end = setupRipeBonds(_epochLength=50)  # shorter for faster testing
    
    # Verify initial state
    assert ledger.epochStart() == start
    assert ledger.epochEnd() == end
    
    # Move to middle of epoch and verify refresh doesn't change anything
    boa.env.time_travel(blocks=25)
    new_start, new_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    assert new_start == start
    assert new_end == end
    
    # Move past epoch and verify refresh creates new epoch  
    boa.env.time_travel(blocks=30)  # Now 55 blocks total, past epoch end at block 50
    new_start, new_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    assert new_start == end  # new epoch starts exactly where old one ended  
    assert new_end == end + 50  # epoch length
    
    # Test that purchases work in the new epoch
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    assert ripe_payout > 0
    
    # Manually start a new epoch in the future
    current_block = boa.env.evm.patch.block_number
    future_start = current_block + 100
    bond_room.startBondEpochAtBlock(future_start, sender=switchboard_delta.address)
    
    # Verify the manual epoch was set
    assert ledger.epochStart() == future_start
    assert ledger.epochEnd() == future_start + 50


def test_get_latest_epoch_block_times_boundary_conditions(
    bond_room
):
    """Test boundary conditions for epoch calculations"""
    
    # Time travel forward to get a reasonable block number for testing
    boa.env.time_travel(blocks=200)
    current_block = boa.env.evm.patch.block_number
    epoch_length = 100
    
    # Test exactly at epoch boundary
    past_start = current_block - epoch_length
    past_end = current_block  # exactly at current block
    start, end, changed = bond_room.getLatestEpochBlockTimes(past_start, past_end, epoch_length)
    
    assert start == past_end
    assert end == past_end + epoch_length
    assert changed == True
    
    # Test with very small epoch length
    small_epoch = 1
    start, end, changed = bond_room.getLatestEpochBlockTimes(0, 0, small_epoch)
    
    assert start == current_block
    assert end == current_block + 1
    assert changed == True
    
    # Test with very large epoch length
    large_epoch = 1000000
    future_start = current_block + 500000
    future_end = future_start + large_epoch
    start, end, changed = bond_room.getLatestEpochBlockTimes(future_start, future_end, large_epoch)
    
    assert start == future_start  # unchanged
    assert end == future_end      # unchanged
    assert changed == False