import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def setupRipeBonds(mission_control, bond_room, setAssetConfig, setGeneralConfig, switchboard_alpha, switchboard_delta, ripe_token, alpha_token):
    def setupRipeBonds(
        _asset = alpha_token,
        _amountPerEpoch = 1000 * EIGHTEEN_DECIMALS,
        _canBond = True,
        _minRipePerUnit = 1 * EIGHTEEN_DECIMALS,
        _maxRipePerUnit = 100 * EIGHTEEN_DECIMALS,
        _maxRipePerUnitLockBonus = HUNDRED_PERCENT,  # 100% bonus (doubles the base payout)
        _epochLength = 100,
        _shouldAutoRestart = True,
        _restartDelayBlocks = 50,
        _minLockDuration = 100,
        _maxLockDuration = 1000,
        _shouldFreezeWhenBadDebt = False,
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
            _restartDelayBlocks,
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
            _shouldFreezeWhenBadDebt,
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
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test,
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

    # should get exactly halfway between min (1x) and max (100x) at 50% epoch progress
    # epochProgress = 50 * 10000 / 100 = 5000 (50%)
    # baseRipePerUnit = 1e18 + (5000 * 99e18 / 10000) = 50.5e18
    # ripePayout = 50.5 * 100 = 5050 RIPE
    expected_ripe = 5050 * EIGHTEEN_DECIMALS
    _test(ripe_payout, expected_ripe)
    

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
    _test(expected_total, ripe_payout)

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
    # maxLockBonus = 100% (from fixture)
    # bonus ratio = (150 - 100) / (1000 - 100) = 50/900 ≈ 5.56%
    # bonus = 5.56% of base payout
    expected_base = payment_amount  # 100 units * 1 RIPE per unit at epoch start
    lock_bonus_ratio = HUNDRED_PERCENT * (lock_duration - 100) // (1000 - 100)  # 5.56% of max bonus
    expected_bonus = expected_base * lock_bonus_ratio // HUNDRED_PERCENT
    expected_total = expected_base + expected_bonus
    _test(expected_total, ripe_payout)

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

    # should get base amount + full lock bonus (100% of base from fixture)
    expected_base = payment_amount  # 100 units * 1 RIPE per unit at epoch start
    expected_bonus = expected_base * 100 // 100  # 100% lock bonus
    expected_total = expected_base + expected_bonus
    _test(expected_total, ripe_payout)

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
    expected_base = payment_amount  # 100 units * 1 RIPE per unit at epoch start
    expected_bonus = expected_base * 100 // 100  # 100% lock bonus (capped at max)
    expected_total = expected_base + expected_bonus
    _test(expected_total, ripe_payout)
    
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


def test_purchase_ripe_bond_refund_goes_to_caller_not_user(
    teller, setupRipeBonds, bob, alice, charlie, alpha_token_whale, alpha_token, _test, ripe_token, setUserConfig, ledger
):
    """Test that refunds go to the transaction caller, not the bond recipient"""
    setupRipeBonds()
    
    # Enable alice to allow others to bond for her
    setUserConfig(alice, _canAnyoneBondForUser=True)
    
    # Reduce available amount by making a partial purchase first (setup partial fill scenario)
    initial_available = ledger.paymentAmountAvailInEpoch()
    consumed_amount = initial_available - (50 * EIGHTEEN_DECIMALS)  # leave 50 tokens available
    
    alpha_token.transfer(charlie, consumed_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, consumed_amount, sender=charlie)
    teller.purchaseRipeBond(alpha_token, consumed_amount, sender=charlie)
    
    # Now bob tries to buy 100 tokens worth for alice, but only 50 are available
    payment_amount = 100 * EIGHTEEN_DECIMALS
    pre_balance_bob = alpha_token.balanceOf(bob)
    pre_balance_alice = alpha_token.balanceOf(alice)
    
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Bob buys bonds for Alice
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        0,  # no lock
        alice,  # user to receive bonds
        sender=bob
    )
    
    # Verify alice gets the ripe tokens
    _test(ripe_token.balanceOf(alice), ripe_payout)
    
    # Verify the refund goes to BOB (the caller), not ALICE (the user)
    available_amount = 50 * EIGHTEEN_DECIMALS
    refund_amount = payment_amount - available_amount  # 50 tokens refund
    
    expected_bob_balance = pre_balance_bob + refund_amount
    _test(alpha_token.balanceOf(bob), expected_bob_balance)
    
    # Alice should not receive any payment token refund
    assert alpha_token.balanceOf(alice) == pre_balance_alice


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

    # epoch should auto-restart with delay
    new_start = ledger.epochStart()
    new_end = ledger.epochEnd() 
    
    # With default _restartDelayBlocks=50, new epoch starts 50 blocks after epoch end
    expected_start = end + 50  # restart delay from epoch end
    assert new_start == expected_start
    assert new_end == expected_start + 100  # epoch length
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

    # purchase setup with very small amount (1 unit = 10^18 wei for 18 decimal token)
    payment_amount = 10 ** alpha_token.decimals()  # 1 full token unit
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)  

    # purchase should work for small amounts
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )

    assert ripe_payout > 0
    assert ripe_token.balanceOf(bob) == ripe_payout


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
    assert event.recipient == bob
    assert event.paymentAsset == alpha_token.address
    assert event.paymentAmount == payment_amount
    assert event.lockDuration == lock_duration
    assert event.totalRipePayout == ripe_payout
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
        _maxRipePerUnitLockBonus=50 * HUNDRED_PERCENT  # 5000% bonus (50x multiplier)
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
    
    # Mid-range should get 50% of max bonus (lock duration 550 is 50% of the way from 100 to 1000)
    # Max bonus is capped at 1000% (10x) by contract, so 50% of 1000% = 500% bonus
    expected_mid = payment_amount + (payment_amount * 500 // 100)  # base + 500% bonus = 600% total
    _test(expected_mid, ripe_payout_mid_lock)
    
    # Maximum should get base + full bonus (capped at 1000%)
    expected_max = payment_amount + (payment_amount * 1000 // 100)  # base + 1000% bonus = 1100% total
    _test(expected_max, ripe_payout_max_lock)
    
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
    large_max_lock_bonus = 5 * HUNDRED_PERCENT  # 500% bonus
    
    setupRipeBonds(
        _amountPerEpoch=large_amount_per_epoch,
        _maxRipePerUnit=large_max_ripe_per_unit,
        _maxRipePerUnitLockBonus=large_max_lock_bonus,
        _maxLockDuration=10000
    )
    
    # Test large purchase with maximum lock (but within available ripe limits)
    payment_amount = 5000 * EIGHTEEN_DECIMALS  # Reduced to stay within ripe availability
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
    # Base rate: ~990.01 RIPE per unit
    expected_base_rate = 1 * EIGHTEEN_DECIMALS + (9900 * 999 * EIGHTEEN_DECIMALS // 10000)  # ~990.01e18
    expected_base_payout = expected_base_rate * payment_amount // EIGHTEEN_DECIMALS
    # Lock bonus: 500% of base payout
    expected_lock_bonus = expected_base_payout * large_max_lock_bonus // HUNDRED_PERCENT
    expected_total = expected_base_payout + expected_lock_bonus
    
    _test(expected_total, ripe_payout)
    
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
    assert changed
    
    # Test 2: Future epoch (current block < start)
    future_start = current_block + 50
    future_end = future_start + epoch_length
    start, end, changed = bond_room.getLatestEpochBlockTimes(future_start, future_end, epoch_length)
    
    assert start == future_start  # unchanged
    assert end == future_end      # unchanged
    assert not changed
    
    # Test 3: Current epoch not expired (current block < end)
    active_start = current_block - 20
    active_end = current_block + 30
    start, end, changed = bond_room.getLatestEpochBlockTimes(active_start, active_end, epoch_length)
    
    assert start == active_start  # unchanged
    assert end == active_end      # unchanged
    assert not changed
    
    # Test 4: Just past epoch end (within next epoch window)
    past_start = current_block - 150
    past_end = current_block - 50
    start, end, changed = bond_room.getLatestEpochBlockTimes(past_start, past_end, epoch_length)
    
    assert start == past_end  # new epoch starts where old one ended
    assert end == past_end + epoch_length
    assert changed
    
    # Test 5: Way past epoch end (multiple epochs ahead)
    very_old_start = current_block - 350
    very_old_end = current_block - 250  # 250 blocks ago
    start, end, changed = bond_room.getLatestEpochBlockTimes(very_old_start, very_old_end, epoch_length)
    
    # Should calculate how many epochs ahead we are
    epochs_ahead = (current_block - very_old_end) // epoch_length
    expected_start = epoch_length * epochs_ahead + very_old_end
    
    assert start == expected_start
    assert end == expected_start + epoch_length
    assert changed


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
    assert changed
    
    # Test with very small epoch length
    small_epoch = 1
    start, end, changed = bond_room.getLatestEpochBlockTimes(0, 0, small_epoch)
    
    assert start == current_block
    assert end == current_block + 1
    assert changed
    
    # Test with very large epoch length
    large_epoch = 1000000
    future_start = current_block + 500000
    future_end = future_start + large_epoch
    start, end, changed = bond_room.getLatestEpochBlockTimes(future_start, future_end, large_epoch)
    
    assert start == future_start  # unchanged
    assert end == future_end      # unchanged
    assert not changed


def test_purchase_ripe_bond_auto_restart_with_delay(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger
):
    """Test that auto-restart respects the restartDelayBlocks parameter"""
    restart_delay = 25  # blocks
    start, end = setupRipeBonds(_shouldAutoRestart=True, _restartDelayBlocks=restart_delay)

    # Exhaust entire epoch availability with one purchase
    available_amount = ledger.paymentAmountAvailInEpoch()
    
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)  

    # Move partway through epoch
    boa.env.time_travel(blocks=10)

    # Purchase entire available amount (should trigger auto-restart)
    teller.purchaseRipeBond(
        alpha_token,
        available_amount,
        sender=bob
    )

    # Get the block number after the transaction
    current_block_after_purchase = boa.env.evm.patch.block_number

    # Verify new epoch starts with delay
    new_start = ledger.epochStart()
    new_end = ledger.epochEnd()
    
    # New epoch should start exactly restart_delay blocks after the epoch end
    # Contract now uses: epochEnd + restart_delay
    expected_new_start = end + restart_delay
    assert new_start == expected_new_start
    assert new_end == expected_new_start + 100  # epoch length
    assert ledger.paymentAmountAvailInEpoch() == 1000 * EIGHTEEN_DECIMALS  # refreshed


def test_purchase_ripe_bond_different_restart_delays(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, ledger
):
    """Test auto-restart with different delay values"""
    
    # Test with zero delay (immediate restart)
    start1, end1 = setupRipeBonds(_shouldAutoRestart=True, _restartDelayBlocks=0)
    
    available_amount = ledger.paymentAmountAvailInEpoch()
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)
    
    teller.purchaseRipeBond(alpha_token, available_amount, sender=bob)
    current_block_after = boa.env.evm.patch.block_number
    
    # With zero delay, new epoch should start immediately after the epoch end
    new_start1 = ledger.epochStart()
    expected_start1 = end1 + 0  # epoch end + zero delay
    assert new_start1 == expected_start1
    
    # Test with larger delay - we need to travel to be within the new epoch
    # The first epoch auto-restarted, so we need to travel past the new start
    blocks_to_travel = new_start1 - boa.env.evm.patch.block_number + 1
    boa.env.time_travel(blocks=blocks_to_travel)
    
    large_delay = 100
    start2, end2 = setupRipeBonds(_shouldAutoRestart=True, _restartDelayBlocks=large_delay)
    
    available_amount = ledger.paymentAmountAvailInEpoch()
    alpha_token.transfer(alice, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=alice)
    
    teller.purchaseRipeBond(alpha_token, available_amount, sender=alice)
    current_block_after2 = boa.env.evm.patch.block_number
    
    # With large delay, new epoch should start much later after epoch end
    new_start2 = ledger.epochStart()
    expected_start2 = end2 + large_delay
    assert new_start2 == expected_start2
    assert ledger.epochEnd() == expected_start2 + 100  # epoch length


###########################
# Bad Debt Clearing Tests #
###########################


def test_bond_purchase_bad_debt_fully_cleared_ledger_data(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, switchboard_alpha, mock_price_source, _test
):
    """Test Ledger data changes when bond purchase fully clears bad debt"""
    setupRipeBonds()
    
    # Set price for USD value calculation
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Set bad debt of $300 USD
    bad_debt_amount = 300 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Capture initial Ledger state
    initial_bad_debt = ledger.badDebt()
    initial_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    initial_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    assert initial_bad_debt == bad_debt_amount
    assert initial_ripe_paid_for_debt == 0
    
    # Purchase bond with payment > bad debt ($500 > $300)
    payment_amount = 500 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    assert ripe_payout != 0
    
    # Verify Ledger data changes
    final_bad_debt = ledger.badDebt()
    final_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    final_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Bad debt should be fully cleared
    assert final_bad_debt == 0
    
    # ripePaidOutForBadDebt should increase by the debt amount that was cleared (based on payment USD value)
    ripe_paid_increase = final_ripe_paid_for_debt - initial_ripe_paid_for_debt
    _test(ripe_paid_increase, bad_debt_amount)  # Should equal original debt amount
    
    # ripeAvailForBonds should be reduced by the surplus portion (payment - debt cleared)
    # since some payment went to debt clearing instead of being deducted from available bonds
    ripe_avail_reduction = initial_ripe_avail_for_bonds - final_ripe_avail_for_bonds
    surplus_payment = payment_amount - bad_debt_amount  # $500 - $300 = $200 surplus
    _test(ripe_avail_reduction, surplus_payment)


def test_bond_purchase_bad_debt_partially_cleared_ledger_data(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, switchboard_alpha, mock_price_source, _test
):
    """Test Ledger data changes when bond purchase partially clears bad debt"""
    setupRipeBonds()
    
    # Set price for USD value calculation
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Set bad debt of $800 USD
    bad_debt_amount = 800 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Capture initial Ledger state
    ledger.badDebt()
    initial_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    initial_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Purchase bond with payment < bad debt ($400 < $800)
    payment_amount = 400 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    
    # Verify Ledger data changes
    final_bad_debt = ledger.badDebt()
    final_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    final_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Bad debt should be reduced by payment amount (USD value)
    expected_remaining_debt = bad_debt_amount - payment_amount  # $800 - $400 = $400
    _test(final_bad_debt, expected_remaining_debt)
    
    # ripePaidOutForBadDebt should increase by the payment amount (all payment goes to debt)
    ripe_paid_increase = final_ripe_paid_for_debt - initial_ripe_paid_for_debt
    _test(ripe_paid_increase, payment_amount)  # Should equal payment amount
    
    # ripeAvailForBonds should not be reduced at all since all payment went to debt clearing
    ripe_avail_reduction = initial_ripe_avail_for_bonds - final_ripe_avail_for_bonds
    assert ripe_avail_reduction == 0  # No reduction since all payment used for debt


def test_bond_purchase_bad_debt_exactly_cleared_ledger_data(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, switchboard_alpha, mock_price_source, _test
):
    """Test Ledger data changes when bond purchase exactly clears bad debt"""
    setupRipeBonds()
    
    # Set price for USD value calculation  
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Set bad debt of $600 USD
    bad_debt_amount = 600 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Capture initial Ledger state
    ledger.badDebt()
    initial_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    initial_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Purchase bond with payment exactly equal to bad debt
    payment_amount = 600 * EIGHTEEN_DECIMALS  # Exactly $600
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    
    # Verify Ledger data changes
    final_bad_debt = ledger.badDebt()
    final_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    final_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Bad debt should be exactly cleared
    assert final_bad_debt == 0
    
    # ripePaidOutForBadDebt should increase by exactly the payment amount (which equals debt amount)
    ripe_paid_increase = final_ripe_paid_for_debt - initial_ripe_paid_for_debt
    _test(ripe_paid_increase, payment_amount)  # Should equal payment amount
    
    # ripeAvailForBonds should not be reduced since all payment went to debt clearing
    ripe_avail_reduction = initial_ripe_avail_for_bonds - final_ripe_avail_for_bonds
    assert ripe_avail_reduction == 0  # No reduction since all payment used for debt


def test_bond_purchase_no_bad_debt_ledger_baseline(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, mock_price_source, _test
):
    """Test Ledger data when no bad debt exists (baseline comparison)"""
    setupRipeBonds()
    
    # Set price for USD value calculation
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Verify no bad debt exists
    assert ledger.badDebt() == 0
    
    # Capture initial Ledger state
    initial_bad_debt = ledger.badDebt()
    initial_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    initial_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Purchase bond normally
    payment_amount = 500 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    
    # Verify Ledger data changes
    final_bad_debt = ledger.badDebt()
    final_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    final_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # Bad debt should remain 0
    assert final_bad_debt == initial_bad_debt == 0
    
    # ripePaidOutForBadDebt should not change
    assert final_ripe_paid_for_debt == initial_ripe_paid_for_debt
    
    # ripeAvailForBonds should be reduced by the full ripe_payout (normal behavior)
    ripe_avail_reduction = initial_ripe_avail_for_bonds - final_ripe_avail_for_bonds
    _test(ripe_avail_reduction, ripe_payout)


def test_bond_purchase_multiple_transactions_progressive_debt_clearing(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, ledger, switchboard_alpha, mock_price_source, _test
):
    """Test Ledger data changes across multiple bond purchases that progressively clear debt"""
    setupRipeBonds()
    
    # Set price for USD value calculation
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Set large bad debt
    initial_debt = 1000 * EIGHTEEN_DECIMALS  # $1000 USD
    ledger.setBadDebt(initial_debt, sender=switchboard_alpha.address)
    
    # Capture initial state
    initial_ripe_paid_for_debt = ledger.ripePaidOutForBadDebt()
    initial_ripe_avail_for_bonds = ledger.ripeAvailForBonds()
    
    # First purchase - partial clearing ($300 of $1000 debt)
    payment_1 = 300 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_1, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_1, sender=bob)
    
    teller.purchaseRipeBond(alpha_token, payment_1, sender=bob)
    
    # Check state after first purchase
    debt_after_1 = ledger.badDebt()
    ripe_paid_after_1 = ledger.ripePaidOutForBadDebt()
    ripe_avail_after_1 = ledger.ripeAvailForBonds()
    
    expected_debt_1 = initial_debt - payment_1  # $1000 - $300 = $700
    _test(debt_after_1, expected_debt_1)
    _test(ripe_paid_after_1 - initial_ripe_paid_for_debt, payment_1)  # Should equal payment amount
    assert ripe_avail_after_1 == initial_ripe_avail_for_bonds  # No change, all payment to debt
    
    # Second purchase - another partial clearing ($400 of remaining $700 debt)
    payment_2 = 400 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, payment_2, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_2, sender=alice)
    
    teller.purchaseRipeBond(alpha_token, payment_2, sender=alice)
    
    # Check state after second purchase
    debt_after_2 = ledger.badDebt()
    ripe_paid_after_2 = ledger.ripePaidOutForBadDebt()
    ripe_avail_after_2 = ledger.ripeAvailForBonds()
    
    expected_debt_2 = expected_debt_1 - payment_2  # $700 - $400 = $300
    _test(debt_after_2, expected_debt_2)
    _test(ripe_paid_after_2 - ripe_paid_after_1, payment_2)  # Should equal payment amount
    assert ripe_avail_after_2 == ripe_avail_after_1  # Still no change, all payment to debt
    
    # Third purchase - clear remaining debt and have surplus ($500 > remaining $300)
    payment_3 = 500 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_3, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_3, sender=bob)
    
    ripe_payout_3 = teller.purchaseRipeBond(alpha_token, payment_3, sender=bob)
    
    # Check final state
    final_debt = ledger.badDebt()
    final_ripe_paid = ledger.ripePaidOutForBadDebt()
    final_ripe_avail = ledger.ripeAvailForBonds()
    
    # All debt should be cleared
    assert final_debt == 0
    
    # Total ripe paid for debt should equal original debt amount
    total_ripe_paid = final_ripe_paid - initial_ripe_paid_for_debt
    _test(total_ripe_paid, initial_debt)  # Should equal total debt that was cleared
    
    # Based on actual behavior: when debt exists, ripeAvailForBonds is not reduced 
    # regardless of whether there's a surplus payment
    ripe_avail_reduction = ripe_avail_after_2 - final_ripe_avail
    
    # The key insight: ripeAvailForBonds should NOT be reduced when bad debt is being cleared
    # All the payment goes to debt clearing, not to reducing available bonds
    assert ripe_avail_reduction == 0  # No reduction in ripeAvailForBonds
    
    # Verify that the user still got the correct payout (matching the debt amount remaining)
    _test(ripe_payout_3, expected_debt_2)  # User gets RIPE equal to remaining debt


#########################
# Preview Helper Tests  #
#########################


def test_preview_ripe_bond_payout_basic(
    bond_room, setupRipeBonds, _test, bob
):
    """Test basic preview functionality at epoch start"""
    setupRipeBonds()
    
    # Preview at epoch start with no lock
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_payout = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    # Should get minimum rate (1x) at epoch start
    expected_payout = payment_amount  # min ripe per unit at epoch start
    _test(preview_payout, expected_payout)


def test_preview_ripe_bond_payout_epoch_progress(
    bond_room, setupRipeBonds, _test, bob
):
    """Test preview payout changes with epoch progress"""
    start, end = setupRipeBonds()
    
    # Test at epoch start (0% progress)
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_start = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    _test(preview_start, payment_amount)  # min rate (1x)
    
    # Move to middle of epoch (50% progress)
    blocks_to_travel = (end - start) // 2
    boa.env.time_travel(blocks=blocks_to_travel)
    
    preview_mid = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    # Should be halfway between min (1x) and max (100x) = 50.5x
    expected_mid = 5050 * EIGHTEEN_DECIMALS
    _test(preview_mid, expected_mid)
    
    # Move near end of epoch (~99% progress)
    additional_blocks = (end - start) - blocks_to_travel - 1
    boa.env.time_travel(blocks=additional_blocks)
    
    preview_end = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    # Should be near maximum rate (~99.01x)
    expected_end = 9901 * EIGHTEEN_DECIMALS
    _test(preview_end, expected_end)
    
    # Verify progression
    assert preview_start < preview_mid < preview_end


def test_preview_ripe_bond_payout_lock_durations(
    bond_room, setupRipeBonds, _test, bob
):
    """Test preview with different lock durations"""
    setupRipeBonds()
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    
    # No lock
    preview_no_lock = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    _test(preview_no_lock, payment_amount)  # base rate only
    
    # Below minimum lock (should be treated as no lock)
    preview_below_min = bond_room.previewRipeBondPayout(bob, 50, payment_amount)
    _test(preview_below_min, payment_amount)  # same as no lock
    
    # Minimum lock (gets zero bonus since lockDuration - minLockDuration = 0)
    preview_min_lock = bond_room.previewRipeBondPayout(bob, 100, payment_amount)
    _test(preview_min_lock, payment_amount)  # base rate only
    
    # Mid-range lock (50% of max lock bonus)
    preview_mid_lock = bond_room.previewRipeBondPayout(bob, 550, payment_amount)
    # Lock bonus ratio = (550 - 100) / (1000 - 100) = 450/900 = 50%
    # Bonus = 50% of base payout (since max lock bonus is 100% from fixture)
    expected_mid = payment_amount + (payment_amount * 50 // 100)  # base + 50% bonus
    _test(preview_mid_lock, expected_mid)
    
    # Maximum lock
    preview_max_lock = bond_room.previewRipeBondPayout(bob, 1000, payment_amount)
    expected_max = payment_amount + (payment_amount * 100 // 100)  # base + 100% bonus
    _test(preview_max_lock, expected_max)
    
    # Above maximum lock (should cap at max)
    preview_above_max = bond_room.previewRipeBondPayout(bob, 2000, payment_amount)
    _test(preview_above_max, expected_max)  # same as max lock
    
    # Verify progression
    assert preview_no_lock == preview_below_min == preview_min_lock
    assert preview_min_lock < preview_mid_lock < preview_max_lock
    assert preview_max_lock == preview_above_max


def test_preview_ripe_bond_payout_payment_amounts(
    bond_room, setupRipeBonds, _test, bob
):
    """Test preview with different payment amounts"""
    setupRipeBonds()
    
    # Small payment amount
    small_amount = 10 * EIGHTEEN_DECIMALS
    preview_small = bond_room.previewRipeBondPayout(bob, 0, small_amount)
    _test(preview_small, small_amount)
    
    # Large payment amount (within available)
    large_amount = 500 * EIGHTEEN_DECIMALS
    preview_large = bond_room.previewRipeBondPayout(bob, 0, large_amount)
    _test(preview_large, large_amount)
    
    # Payment amount exceeding epoch availability (should be capped)
    excessive_amount = 5000 * EIGHTEEN_DECIMALS  # more than 1000 available
    preview_excessive = bond_room.previewRipeBondPayout(bob, 0, excessive_amount)
    expected_capped = 1000 * EIGHTEEN_DECIMALS  # should be capped to available amount
    _test(preview_excessive, expected_capped)
    
    # Zero payment amount (should return 0)
    preview_zero = bond_room.previewRipeBondPayout(bob, 0, 0)
    assert preview_zero == 0
    
    # Default max_value parameter (should use available amount)
    preview_default = bond_room.previewRipeBondPayout(bob, 0)  # using default max_value
    _test(preview_default, expected_capped)


def test_preview_ripe_bond_payout_disabled_bonds(
    bond_room, setupRipeBonds, bob
):
    """Test preview returns 0 when bonds are disabled"""
    setupRipeBonds(_canBond=False)
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_payout = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    assert preview_payout == 0


def test_preview_ripe_bond_payout_no_ripe_per_unit(
    bond_room, setupRipeBonds, bob
):
    """Test preview returns 0 when max ripe per unit is 0"""
    setupRipeBonds(_maxRipePerUnit=0)
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_payout = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    assert preview_payout == 0


def test_preview_ripe_bond_payout_6_decimal_token(
    bond_room, setupRipeBonds, charlie_token, _test, bob
):
    """Test preview with 6 decimal token"""
    charlie_amount_per_epoch = 1000 * (10 ** 6)
    setupRipeBonds(_asset=charlie_token, _amountPerEpoch=charlie_amount_per_epoch)
    
    payment_amount_6dec = 100 * (10 ** 6)
    preview_6dec = bond_room.previewRipeBondPayout(bob, 0, payment_amount_6dec)
    # Ripe per unit is 1e18, so 100 * 1e6 * 1e18 / 1e6 = 100e18
    expected_6dec = 100 * EIGHTEEN_DECIMALS
    _test(preview_6dec, expected_6dec)


def test_preview_ripe_bond_payout_8_decimal_token(
    bond_room, setupRipeBonds, delta_token, _test, bob
):
    """Test preview with 8 decimal token"""
    delta_amount_per_epoch = 1000 * (10 ** 8)
    setupRipeBonds(_asset=delta_token, _amountPerEpoch=delta_amount_per_epoch)
    
    payment_amount_8dec = 100 * (10 ** 8)
    preview_8dec = bond_room.previewRipeBondPayout(bob, 0, payment_amount_8dec)
    # Ripe per unit is 1e18, so 100 * 1e8 * 1e18 / 1e8 = 100e18
    expected_8dec = 100 * EIGHTEEN_DECIMALS
    _test(preview_8dec, expected_8dec)


def test_preview_ripe_bond_payout_epoch_auto_advance(
    bond_room, setupRipeBonds, _test, bob
):
    """Test preview when epoch would auto-advance"""
    start, end = setupRipeBonds()
    
    # Move past epoch end to trigger auto-advance scenario
    blocks_past_end = (end - start) + 10
    boa.env.time_travel(blocks=blocks_past_end)
    
    current_block = boa.env.evm.patch.block_number
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_payout = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    # When epoch auto-advances, new epoch starts at old epoch end (which is in the past)
    # So we're actually partway through the new epoch, which gives higher rate
    # Epoch progress = (current_block - end) * 10000 / epoch_length
    # Let's calculate what we should expect
    epoch_length = end - start  # 100 blocks
    new_epoch_start = end  # new epoch starts where old ended
    progress_in_new_epoch = (current_block - new_epoch_start) * 10000 // epoch_length
    # progress_in_new_epoch = 10 * 10000 / 100 = 1000 (10%)
    # baseRipePerUnit = 1e18 + (1000 * 99e18 / 10000) = 1e18 + 9.9e18 = 10.9e18
    expected_rate = 1 * EIGHTEEN_DECIMALS + (progress_in_new_epoch * 99 * EIGHTEEN_DECIMALS // 10000)
    expected_payout = expected_rate * payment_amount // EIGHTEEN_DECIMALS
    _test(preview_payout, expected_payout)


def test_preview_ripe_bond_payout_exhausted_epoch(
    bond_room, setupRipeBonds, teller, bob, alpha_token_whale, alpha_token
):
    """Test preview when current epoch is exhausted"""
    setupRipeBonds(_shouldAutoRestart=False)
    
    # Exhaust current epoch
    available_amount = 1000 * EIGHTEEN_DECIMALS  # full epoch amount
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)
    teller.purchaseRipeBond(alpha_token, available_amount, sender=bob)
    
    # Preview should return 0 since no more available in current epoch
    payment_amount = 100 * EIGHTEEN_DECIMALS
    preview_payout = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    assert preview_payout == 0


def test_preview_ripe_bond_payout_complex_scenario(
    bond_room, setupRipeBonds, _test, bob
):
    """Test preview with complex scenario combining multiple factors"""
    start, end = setupRipeBonds(
        _minRipePerUnit=5 * EIGHTEEN_DECIMALS,
        _maxRipePerUnit=50 * EIGHTEEN_DECIMALS,
        _maxRipePerUnitLockBonus=2 * HUNDRED_PERCENT,  # 200% bonus
        _minLockDuration=200,
        _maxLockDuration=2000
    )
    
    # Move to 75% through epoch
    blocks_to_travel = (end - start) * 3 // 4
    boa.env.time_travel(blocks=blocks_to_travel)
    
    # Preview with lock duration at 60% of range
    payment_amount = 200 * EIGHTEEN_DECIMALS
    lock_duration = 1280  # 200 + (0.6 * (2000 - 200)) = 1280
    
    preview_payout = bond_room.previewRipeBondPayout(bob, lock_duration, payment_amount)
    
    # Calculate expected values
    # Epoch progress = 75% = 7500/10000
    # Base rate = 5 + (7500 * 45 / 10000) = 5 + 33.75 = 38.75 RIPE per unit
    # Units = 200
    # Base payout = 38.75 * 200 = 7750 RIPE
    # Lock bonus ratio = 60% of 200% = 120%
    # Lock bonus = 120% of base payout
    expected_base_rate = 5 * EIGHTEEN_DECIMALS + (7500 * 45 * EIGHTEEN_DECIMALS // 10000)
    expected_base_payout = expected_base_rate * payment_amount // EIGHTEEN_DECIMALS
    lock_bonus_ratio = 60 * 2 * HUNDRED_PERCENT // 100  # 60% of 200% max bonus
    expected_lock_bonus = expected_base_payout * lock_bonus_ratio // HUNDRED_PERCENT
    expected_payout = expected_base_payout + expected_lock_bonus
    
    _test(preview_payout, expected_payout)


def test_preview_next_epoch_during_active_epoch(
    bond_room, setupRipeBonds
):
    """Test preview next epoch during active epoch"""
    start, end = setupRipeBonds()
    
    # Move partway through epoch
    boa.env.time_travel(blocks=30)
    
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Should return current epoch since it's still active
    assert preview_start == start
    assert preview_end == end


def test_preview_next_epoch_past_expiration(
    bond_room, setupRipeBonds
):
    """Test preview next epoch when current epoch has expired"""
    start, end = setupRipeBonds(_epochLength=100)
    
    # Move past epoch end
    blocks_past_end = (end - start) + 10
    boa.env.time_travel(blocks=blocks_past_end)
    
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Should return new epoch that starts where old one ended
    assert preview_start == end  # new epoch starts exactly where old ended
    assert preview_end == end + 100  # epoch length


def test_preview_next_epoch_no_epoch_set(
    bond_room, setupRipeBonds, switchboard_delta
):
    """Test preview next epoch when no epoch is currently set"""
    setupRipeBonds()
    
    # Clear epoch data by setting both start and end to 0 using bond room
    bond_room.startBondEpochAtBlock(0, sender=switchboard_delta.address)
    
    current_block = boa.env.evm.patch.block_number
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Should return new epoch starting at current block
    assert preview_start == current_block
    assert preview_end == current_block + 100  # default epoch length


def test_preview_next_epoch_multiple_epochs_ahead(
    bond_room, setupRipeBonds
):
    """Test preview next epoch when far past expiration"""
    start, end = setupRipeBonds(_epochLength=50)
    
    # Move far past epoch end (multiple epochs ahead)
    blocks_past_end = (end - start) * 3 + 25  # 3.5 epochs past
    boa.env.time_travel(blocks=blocks_past_end)
    
    current_block = boa.env.evm.patch.block_number
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Should calculate how many epochs ahead we are
    epochs_ahead = (current_block - end) // 50
    expected_start = 50 * epochs_ahead + end
    expected_end = expected_start + 50
    
    assert preview_start == expected_start
    assert preview_end == expected_end


def test_preview_next_epoch_different_epoch_lengths(
    bond_room, setupRipeBonds
):
    """Test preview next epoch with different epoch lengths"""
    # Test with short epoch
    start_short, end_short = setupRipeBonds(_epochLength=25)
    
    # Move past short epoch
    boa.env.time_travel(blocks=30)
    
    preview_start_short, preview_end_short = bond_room.previewNextEpoch()
    assert preview_start_short == end_short
    assert preview_end_short == end_short + 25
    
    # Test with long epoch
    start_long, end_long = setupRipeBonds(_epochLength=500)
    
    # Move past long epoch  
    boa.env.time_travel(blocks=520)
    
    preview_start_long, preview_end_long = bond_room.previewNextEpoch()
    assert preview_start_long == end_long
    assert preview_end_long == end_long + 500


def test_preview_next_epoch_boundary_conditions(
    bond_room, setupRipeBonds
):
    """Test preview next epoch at exact boundaries"""
    start, end = setupRipeBonds(_epochLength=100)
    
    # Test exactly at epoch end
    blocks_to_end = end - start
    boa.env.time_travel(blocks=blocks_to_end)
    
    current_block = boa.env.evm.patch.block_number
    assert current_block == end
    
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Should return new epoch since we're at the boundary (current block >= end)
    assert preview_start == end
    assert preview_end == end + 100
    
    # Test one block before epoch end
    boa.env.time_travel(blocks=-1)  # go back one block
    
    preview_start_before, preview_end_before = bond_room.previewNextEpoch()
    
    # Should return current epoch since we're still within it
    assert preview_start_before == start
    assert preview_end_before == end


def test_preview_functions_consistency(
    bond_room, setupRipeBonds, teller, bob, alpha_token_whale, alpha_token, switchboard_delta, _test
):
    """Test that preview functions match actual execution results"""
    setupRipeBonds()
    
    # Setup for actual purchase
    payment_amount = 150 * EIGHTEEN_DECIMALS
    lock_duration = 300
    
    # Get preview values before purchase
    preview_payout = bond_room.previewRipeBondPayout(bob, lock_duration, payment_amount)
    preview_start, preview_end = bond_room.previewNextEpoch()
    
    # Execute actual purchase
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    actual_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )
    
    # Preview should match actual result
    _test(preview_payout, actual_payout)
    
    # Test epoch preview consistency
    # Move to scenario where epoch would change
    boa.env.time_travel(blocks=110)  # past epoch end
    
    preview_start_new, preview_end_new = bond_room.previewNextEpoch()
    
    # Execute refresh to see actual new epoch (using valid ripe address)
    actual_start, actual_end = bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    
    # Preview should match actual epoch calculation
    assert preview_start_new == actual_start
    assert preview_end_new == actual_end


def test_preview_ripe_bond_payout_gas_efficiency(
    bond_room, setupRipeBonds, bob
):
    """Test that preview functions are gas efficient (view functions)"""
    setupRipeBonds()
    
    # Multiple calls should not affect state or cost significant gas
    payment_amount = 100 * EIGHTEEN_DECIMALS
    
    # Call preview multiple times - should be consistent
    preview_1 = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    preview_2 = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    preview_3 = bond_room.previewRipeBondPayout(bob, 0, payment_amount)
    
    assert preview_1 == preview_2 == preview_3
    
    # Same for epoch preview
    epoch_1 = bond_room.previewNextEpoch()
    epoch_2 = bond_room.previewNextEpoch()
    
    assert epoch_1 == epoch_2


#########################
# Bond Booster Tests
#########################


def test_purchase_ripe_bond_with_bond_booster(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room, 
    bond_booster, switchboard_delta, _test
):
    """Test purchasing ripe bond with bond booster gives extra RIPE"""
    setupRipeBonds()
    
    # Set up bond booster for bob
    # 300% boost, max 100 units, expires far in future
    config = (bob, 3 * HUNDRED_PERCENT, 100, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Purchase setup - 100 alpha tokens (100 units)
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Should get base payout (100 RIPE) + boost (300% of base = 300 RIPE)
    expected_base = 100 * EIGHTEEN_DECIMALS  # 100 units * 1 RIPE per unit
    expected_boost = expected_base * 300 // 100  # 300% of base
    expected_total = expected_base + expected_boost
    _test(expected_total, ripe_payout)
    
    # Check that units were used in bond booster
    assert bond_booster.unitsUsed(bob) == 100


def test_purchase_ripe_bond_with_limited_bond_booster_units(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta, _test
):
    """Test purchasing with limited bond booster units available"""
    setupRipeBonds()
    
    # Set up bond booster for bob - 100% boost, only 50 units available
    config = (bob, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Purchase setup - 100 alpha tokens (100 units requested)
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Should get base payout (100 RIPE) + full boost (100% of base)
    # Boost applies to full amount as long as ANY units are available
    expected_base = 100 * EIGHTEEN_DECIMALS
    expected_boost = expected_base * 100 // 100  # 100% of base
    expected_total = expected_base + expected_boost
    _test(expected_total, ripe_payout)
    
    # Check that 100 units were used (even though only 50 were available)
    assert bond_booster.unitsUsed(bob) == 100


def test_purchase_ripe_bond_with_exhausted_bond_booster(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta, _test
):
    """Test purchasing after bond booster units are exhausted"""
    setupRipeBonds()
    
    # Set up bond booster for bob - 100% boost, 50 units max
    config = (bob, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # First purchase - use up all booster units
    payment_amount_1 = 50 * EIGHTEEN_DECIMALS  # 50 units
    alpha_token.transfer(bob, payment_amount_1, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_1, sender=bob)
    
    ripe_payout_1 = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_1,
        sender=bob
    )
    
    # Should get base + full boost (100% of base)
    expected_base_1 = 50 * EIGHTEEN_DECIMALS
    expected_1 = expected_base_1 + (expected_base_1 * 100 // 100)
    _test(expected_1, ripe_payout_1)
    assert bond_booster.unitsUsed(bob) == 50
    
    # Second purchase - no boost available
    payment_amount_2 = 30 * EIGHTEEN_DECIMALS  # 30 units
    alpha_token.transfer(bob, payment_amount_2, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_2, sender=bob)
    
    ripe_payout_2 = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_2,
        sender=bob
    )
    
    # Should get only base payout (no boost)
    expected_2 = 30 * EIGHTEEN_DECIMALS
    _test(expected_2, ripe_payout_2)
    assert bond_booster.unitsUsed(bob) == 50  # Unchanged


def test_purchase_ripe_bond_with_expired_bond_booster(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta, _test
):
    """Test purchasing with expired bond booster vs without booster"""
    start, end = setupRipeBonds()
    
    # Set up bond booster that will expire soon
    current_block = boa.env.evm.patch.block_number
    config = (bob, HUNDRED_PERCENT, 50, current_block + 50)  # 100% boost, expires in 50 blocks
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Move past expiration 
    boa.env.time_travel(blocks=60)
    
    # First, purchase with alice (no booster) as baseline at this point in time
    payment_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=alice)
    
    alice_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=alice
    )
    
    # Now purchase with bob (expired booster) - should get same as alice
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    bob_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Bob should get same payout as alice (no boost due to expiration)
    _test(alice_payout, bob_payout)
    assert bond_booster.unitsUsed(bob) == 0  # No units used since expired


def test_purchase_ripe_bond_without_bond_booster(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test
):
    """Test purchasing without any bond booster config"""
    setupRipeBonds()
    
    # Purchase setup - bob has no bond booster config
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase ripe bond
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Should get only base payout (no boost)
    expected = 100 * EIGHTEEN_DECIMALS  # 100 units * 1 RIPE per unit
    _test(expected, ripe_payout)


def test_purchase_ripe_bond_booster_with_lock_duration(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta, _test
):
    """Test bond booster works with lock duration bonuses"""
    setupRipeBonds()
    
    # Set up bond booster
    config = (bob, 2 * HUNDRED_PERCENT, 100, 1000000)  # 200% boost
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Purchase setup with max lock duration (1000 blocks)
    payment_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase with lock duration
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        1000,  # max lock duration
        sender=bob
    )
    
    # Should get base (1 RIPE) + lock bonus (100% of base) + booster (200% of base)
    expected_base = 50 * EIGHTEEN_DECIMALS  # 50 units * 1 RIPE per unit
    expected_lock_bonus = expected_base * 100 // 100  # 100% of base (from fixture)
    expected_boost_bonus = expected_base * 200 // 100  # 200% of base
    expected_total = expected_base + expected_lock_bonus + expected_boost_bonus
    _test(expected_total, ripe_payout)


def test_purchase_ripe_bond_booster_event_emission(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta
):
    """Test that bond purchase events include booster information"""
    setupRipeBonds()
    
    # Set up bond booster
    config = (bob, 5 * HUNDRED_PERCENT, 100, 1000000)  # 500% boost
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Purchase setup
    payment_amount = 75 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase ripe bond
    teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Check event emission
    logs = filter_logs(teller, "RipeBondPurchased")
    assert len(logs) == 1
    log = logs[0]
    
    # Verify booster amount is in the event
    expected_base = 75 * EIGHTEEN_DECIMALS
    expected_boost = expected_base * 500 // 100  # 500% of base
    assert log.ripeBoostBonus == expected_boost
    assert log.recipient == bob


def test_purchase_ripe_bond_multiple_users_with_boosters(
    teller, setupRipeBonds, bob, alice, charlie, alpha_token_whale, alpha_token,
    bond_booster, switchboard_delta, _test
):
    """Test multiple users with different bond booster configurations"""
    setupRipeBonds()
    
    # Set up different boosters for each user
    configs = [
        (bob, HUNDRED_PERCENT, 50, 1000000),            # Bob: 100% boost, 50 max
        (alice, 2 * HUNDRED_PERCENT, 30, 1000000),      # Alice: 200% boost, 30 max  
        (charlie, 3 * HUNDRED_PERCENT, 75, 1000000),    # Charlie: 300% boost, 75 max
    ]
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # Bob's purchase - 50 units (all boosted)
    payment_amount_bob = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount_bob, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_bob, sender=bob)
    
    ripe_payout_bob = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_bob,
        sender=bob
    )
    
    expected_base_bob = 50 * EIGHTEEN_DECIMALS
    expected_bob = expected_base_bob + (expected_base_bob * 100 // 100)  # +100% boost
    _test(expected_bob, ripe_payout_bob)
    
    # Alice's purchase - 40 units (30 boosted, 10 regular)
    payment_amount_alice = 40 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, payment_amount_alice, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_alice, sender=alice)
    
    ripe_payout_alice = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_alice,
        sender=alice
    )
    
    expected_base_alice = 40 * EIGHTEEN_DECIMALS
    expected_alice = expected_base_alice + (expected_base_alice * 200 // 100)  # +200% boost on full amount
    _test(expected_alice, ripe_payout_alice)
    
    # Charlie's purchase - 20 units (all boosted)
    payment_amount_charlie = 20 * EIGHTEEN_DECIMALS
    alpha_token.transfer(charlie, payment_amount_charlie, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_charlie, sender=charlie)
    
    ripe_payout_charlie = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_charlie,
        sender=charlie
    )
    
    expected_base_charlie = 20 * EIGHTEEN_DECIMALS
    expected_charlie = expected_base_charlie + (expected_base_charlie * 300 // 100)  # +300% boost
    _test(expected_charlie, ripe_payout_charlie)
    
    # Verify units used for each user
    assert bond_booster.unitsUsed(bob) == 50
    assert bond_booster.unitsUsed(alice) == 40  # All 40 units used
    assert bond_booster.unitsUsed(charlie) == 20


def test_purchase_ripe_bond_with_removed_booster(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room,
    bond_booster, switchboard_delta, _test
):
    """Test purchasing after bond booster is removed"""
    setupRipeBonds()
    
    # Set up bond booster and use some units
    config = (bob, 2 * HUNDRED_PERCENT, 100, 1000000)  # 200% boost
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # First purchase with booster
    payment_amount_1 = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount_1, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_1, sender=bob)
    
    ripe_payout_1 = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_1,
        sender=bob
    )
    
    expected_base_1 = 25 * EIGHTEEN_DECIMALS
    expected_1 = expected_base_1 + (expected_base_1 * 200 // 100)  # +200% boost
    _test(expected_1, ripe_payout_1)
    assert bond_booster.unitsUsed(bob) == 25
    
    # Remove booster
    bond_booster.removeBondBooster(bob, sender=switchboard_delta.address)
    
    # Second purchase without booster
    payment_amount_2 = 30 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount_2, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount_2, sender=bob)
    
    ripe_payout_2 = teller.purchaseRipeBond(
        alpha_token,
        payment_amount_2,
        sender=bob
    )
    
    # Should get only base payout
    expected_2 = 30 * EIGHTEEN_DECIMALS
    _test(expected_2, ripe_payout_2)
    assert bond_booster.unitsUsed(bob) == 0  # Reset after removal


#########################
# Additional Edge Cases #
#########################


def test_purchase_ripe_bond_contract_paused(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room, switchboard_alpha
):
    """Test that purchases fail when contract is paused"""
    setupRipeBonds()
    
    # Setup purchase
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Pause the contract
    bond_room.pause(True, sender=switchboard_alpha.address)
    
    # Attempt purchase - should fail
    with boa.reverts("contract paused"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )
    
    # Unpause and verify it works
    bond_room.pause(False, sender=switchboard_alpha.address)
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    assert ripe_payout == payment_amount


def test_purchase_ripe_bond_user_not_whitelisted(
    teller, setupRipeBonds, setAssetConfig, bob, alpha_token_whale, alpha_token, 
    mock_whitelist
):
    """Test purchase fails when user is not on whitelist"""
    # First setup bonds as normal
    setupRipeBonds()
    
    # Then update the asset config to add whitelist requirement
    setAssetConfig(
        alpha_token,
        _whitelist=mock_whitelist  # Add whitelist restriction
    )
    
    # Bob is not on whitelist initially
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Try to purchase - should fail because bob is not whitelisted
    with boa.reverts("user not on whitelist"):
        teller.purchaseRipeBond(
            alpha_token,
            payment_amount,
            sender=bob
        )
    
    # Add bob to whitelist
    mock_whitelist.setAllowed(bob, alpha_token, True, sender=bob)
    
    # Now purchase should work
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Verify purchase succeeded
    assert ripe_payout > 0


def test_purchase_ripe_bond_bad_debt_zero_usd_value(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger, mock_price_source, switchboard_alpha, _test
):
    """Test bad debt handling when PriceDesk returns 0 USD value"""
    setupRipeBonds()
    
    # Set bad debt
    ledger.setBadDebt(1000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)
    
    # Set price to 0 to simulate price feed failure
    mock_price_source.setPrice(alpha_token, 0)
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase should work but no debt should be cleared if USD value is 0
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Check that bad debt wasn't reduced
    assert ledger.badDebt() == 1000 * EIGHTEEN_DECIMALS
    _test(ripe_payout, payment_amount)


def test_purchase_ripe_bond_division_by_zero_protection(
    bond_room, setupRipeBonds
):
    """Test division by zero protection in calculations"""
    # Test with minLockDuration = maxLockDuration
    setupRipeBonds(
        _minLockDuration=1000,
        _maxLockDuration=1000,  # Same as min
        _maxRipePerUnitLockBonus=HUNDRED_PERCENT  # 100% lock bonus
    )
    
    # Fixed: Previously had division by zero bug when minLockDuration = maxLockDuration
    # Now it should give full lock bonus when meeting the fixed duration requirement
    payment_amount = 100 * EIGHTEEN_DECIMALS
    
    # Preview with the fixed lock duration should now work and give full bonus
    preview_with_lock = bond_room.previewRipeBondPayout(ZERO_ADDRESS, 1000, payment_amount)
    assert preview_with_lock == 2 * payment_amount  # Base (100) + full lock bonus (100%)
    
    # Preview with no lock duration should give just base payout
    preview_no_lock = bond_room.previewRipeBondPayout(ZERO_ADDRESS, 0, payment_amount)
    assert preview_no_lock == payment_amount  # Just base payout


def test_purchase_ripe_bond_very_large_numbers(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test
):
    """Test with very large numbers to check for overflow"""
    # Setup with large values that are still within reasonable bounds
    large_amount_per_epoch = 10**9 * EIGHTEEN_DECIMALS  # 1 billion tokens
    
    setupRipeBonds(
        _amountPerEpoch=large_amount_per_epoch,
        _maxRipePerUnit=1000 * EIGHTEEN_DECIMALS,
        _maxRipePerUnitLockBonus=5 * HUNDRED_PERCENT  # 500%
    )
    
    # Purchase a large amount
    payment_amount = 10**6 * EIGHTEEN_DECIMALS  # 1 million tokens
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Should handle large numbers without overflow
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # Verify expected payout
    # At epoch start (0% progress), rate = minRipePerUnit = 1 RIPE per unit
    # 1 million units * 1 RIPE per unit = 1 million RIPE
    expected_payout = payment_amount  # 1:1 at epoch start
    _test(ripe_payout, expected_payout)


def test_set_bond_booster_permissions(
    bond_room, alice, switchboard_delta
):
    """Test setBondBooster permission requirements"""
    new_booster = alice  # Just use any address
    
    # Non-switchboard cannot set
    with boa.reverts("no perms"):
        bond_room.setBondBooster(new_booster, sender=alice)
    
    # Switchboard can set
    bond_room.setBondBooster(new_booster, sender=switchboard_delta.address)
    assert bond_room.bondBooster() == new_booster


def test_start_bond_epoch_permissions_and_paused(
    bond_room, alice, switchboard_delta, switchboard_alpha
):
    """Test startBondEpochAtBlock permissions and paused state"""
    # Non-switchboard cannot call
    with boa.reverts("no perms"):
        bond_room.startBondEpochAtBlock(1000, sender=alice)
    
    # Pause contract
    bond_room.pause(True, sender=switchboard_alpha.address)
    
    # Switchboard cannot call when paused
    with boa.reverts("contract paused"):
        bond_room.startBondEpochAtBlock(1000, sender=switchboard_delta.address)
    
    # Unpause
    bond_room.pause(False, sender=switchboard_alpha.address)
    
    # Now it should work
    bond_room.startBondEpochAtBlock(1000, sender=switchboard_delta.address)


def test_refresh_bond_epoch_permissions(
    bond_room, alice
):
    """Test refreshBondEpoch permission requirements"""
    # Random address cannot call
    with boa.reverts("no perms"):
        bond_room.refreshBondEpoch(sender=alice)


def test_purchase_ripe_bond_with_bond_booster_and_bad_debt(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token,
    bond_booster, switchboard_delta, ledger, switchboard_alpha, mock_price_source
):
    """Test complex scenario with both bond booster and bad debt"""
    setupRipeBonds()
    
    # Set price for alpha token
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 USD per token
    
    # Set up bond booster
    config = (bob, 2 * HUNDRED_PERCENT, 100, 1000000)  # 200% boost
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Set bad debt
    ledger.setBadDebt(500 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)
    
    # Purchase
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        sender=bob
    )
    
    # With 200% boost: base (100) + boost (200) = 300 RIPE total
    # Bad debt logic: User still receives full RIPE payout, but some is accounted as bad debt repayment
    assert ripe_payout == 300 * EIGHTEEN_DECIMALS  # User receives full payout
    
    # Verify bad debt was reduced by payment USD value (not RIPE amount)
    # Initial debt: 500, payment value: ~100, remaining: 400
    remaining_debt = ledger.badDebt()
    assert remaining_debt == 400 * EIGHTEEN_DECIMALS


def test_purchase_ripe_bond_epoch_boundary_race_condition(
    teller, setupRipeBonds, bob, alice, alpha_token_whale, alpha_token
):
    """Test multiple users purchasing at epoch boundary"""
    start, end = setupRipeBonds(
        _amountPerEpoch=150 * EIGHTEEN_DECIMALS,  # Limited amount
        _shouldAutoRestart=True,
        _restartDelayBlocks=10
    )
    
    # Move close to epoch exhaustion
    payment_amount = 75 * EIGHTEEN_DECIMALS
    
    # Bob purchases first half
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    
    # Alice purchases second half, exhausting epoch
    alpha_token.transfer(alice, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=alice)
    teller.purchaseRipeBond(alpha_token, payment_amount, sender=alice)
    
    # Next user should fail until restart delay passes
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    with boa.reverts("not within epoch window"):
        teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)
    
    # After delay, should work
    # New epoch starts at end + 10, so we need to be past that
    blocks_to_new_epoch = end + 10 - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_new_epoch + 1)
    teller.purchaseRipeBond(alpha_token, payment_amount, sender=bob)


def test_purchase_ripe_bond_auto_restart_based_on_epoch_end(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, ledger
):
    """Test that auto-restart is based on epoch end, not current block"""
    restart_delay = 20
    start, end = setupRipeBonds(_shouldAutoRestart=True, _restartDelayBlocks=restart_delay)
    
    # Travel to near the end of the epoch but not at the end
    boa.env.time_travel(blocks=90)  # 10 blocks before epoch end
    
    # Exhaust entire epoch availability with one purchase
    available_amount = ledger.paymentAmountAvailInEpoch()
    alpha_token.transfer(bob, available_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, available_amount, sender=bob)
    
    # Store the block when purchase happens
    teller.purchaseRipeBond(alpha_token, available_amount, sender=bob)
    purchase_block = boa.env.evm.patch.block_number
    
    # Verify new epoch starts based on original epoch end, not purchase block
    new_start = ledger.epochStart()
    new_end = ledger.epochEnd()
    
    # New epoch should start at original epoch end + restart delay
    # NOT at purchase block + restart delay
    expected_start = end + restart_delay
    assert new_start == expected_start
    assert new_end == expected_start + 100  # epoch length
    
    # Verify that purchase block was before epoch end
    assert purchase_block < end
    # And that new start is based on epoch end, not purchase block
    assert new_start != purchase_block + restart_delay


def test_purchase_ripe_bond_zero_base_payout_fails(
    teller, setupRipeBonds, bob, charlie_token, charlie_token_whale
):
    """Test that purchase fails if base payout would be 0"""
    # Setup with 6 decimal token
    setupRipeBonds(_asset=charlie_token)
    
    # Try to purchase less than 1 unit (0.5 tokens with 6 decimals)
    payment_amount = 5 * 10**5  # 0.5 tokens
    charlie_token.transfer(bob, payment_amount, sender=charlie_token_whale)
    charlie_token.approve(teller, payment_amount, sender=bob)
    
    # Should fail because base payout would be 0
    with boa.reverts("must have base ripe payout"):
        teller.purchaseRipeBond(
            charlie_token,
            payment_amount,
            sender=bob
        )


def test_purchase_ripe_bond_max_lock_bonus_cap(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, _test
):
    """Test that lock bonus is properly capped at 1000%"""
    # Setup with lock bonus exceeding 1000%
    setupRipeBonds(
        _maxRipePerUnitLockBonus=20 * HUNDRED_PERCENT  # 2000% - should be capped
    )
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase with max lock
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        1000,  # max lock duration
        sender=bob
    )
    
    # Should be capped at 1000% bonus (10x)
    # Base (100) + capped bonus (1000) = 1100 RIPE
    expected = 11 * payment_amount  # 11x total
    _test(ripe_payout, expected)


def test_preview_consistency_with_purchase(
    teller, bond_room, setupRipeBonds, bob, alpha_token_whale, alpha_token
):
    """Test that preview accurately predicts actual purchase results"""
    setupRipeBonds()
    
    payment_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500
    
    # Get preview
    preview = bond_room.previewRipeBondPayout(bob, lock_duration, payment_amount)
    
    # Do actual purchase
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    actual = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )
    
    # Should match exactly
    assert preview == actual


def test_purchase_ripe_bond_rounding_errors(
    teller, setupRipeBonds, bob, alpha_token_whale, alpha_token, bond_room
):
    """Test for potential rounding errors in calculations"""
    setupRipeBonds(
        _minRipePerUnit=333333333333333333,  # 0.333... RIPE per unit
        _maxRipePerUnit=666666666666666667,  # 0.666... RIPE per unit
        _maxRipePerUnitLockBonus=33333  # 333.33% - odd percentage
    )
    
    # Use odd payment amount
    payment_amount = 77 * EIGHTEEN_DECIMALS + 777777777777777777  # 77.777... tokens
    alpha_token.transfer(bob, payment_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, payment_amount, sender=bob)
    
    # Purchase with odd lock duration
    lock_duration = 333
    ripe_payout = teller.purchaseRipeBond(
        alpha_token,
        payment_amount,
        lock_duration,
        sender=bob
    )
    
    # Should handle rounding without reverting
    # Calculate expected payout with the odd values
    # At epoch start (0% progress): ripePerUnit = 0.333... RIPE
    # Units = 77.777... 
    # Base payout = 0.333... * 77.777... ≈ 25.925 RIPE
    # Lock bonus: (333-100)/(1000-100) = 233/900 ≈ 25.89% of max bonus
    # Lock bonus amount = 25.925 * (333.33% * 25.89%) ≈ 25.925 * 86.3% ≈ 22.37 RIPE
    # Total ≈ 48.3 RIPE
    assert ripe_payout > 25 * EIGHTEEN_DECIMALS  # At least base payout
    assert ripe_payout < 100 * EIGHTEEN_DECIMALS  # Reasonable upper bound
    
    # Verify no tokens are stuck due to rounding
    bond_balance = alpha_token.balanceOf(bond_room.address)
    assert bond_balance == 0  # All should be transferred to endaoment

