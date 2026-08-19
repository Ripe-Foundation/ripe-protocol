import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import (
    assert_reverted_call,
    claim_from_stability_pool,
    clear_transient_storage,
    filter_logs,
    redeem_from_stability_pool,
)
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


LAUNCH_MIN_SGREEN_DEPOSIT = 10**16
LAUNCH_PER_USER_SGREEN_LIMIT = 100_000_000 * EIGHTEEN_DECIMALS
LAUNCH_GLOBAL_SGREEN_LIMIT = 1_000_000_000 * EIGHTEEN_DECIMALS
ACTIVATION_THRESHOLD = 10**17


def _configure_launch_sgreen(
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    createDebtTerms,
):
    setGeneralConfig()
    setAssetConfig(
        savings_green,
        [1],
        _perUserDepositLimit=LAUNCH_PER_USER_SGREEN_LIMIT,
        _globalDepositLimit=LAUNCH_GLOBAL_SGREEN_LIMIT,
        _minDepositBalance=LAUNCH_MIN_SGREEN_DEPOSIT,
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
        _canRedeemCollateral=False,
        _canRedeemInStabPool=False,
        _canBuyInAuction=False,
        _canClaimInStabPool=False,
    )


def _convert_and_deposit(teller, green_token, user, amount):
    green_token.approve(teller, amount, sender=user)
    deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(
        user,
        amount,
        sender=user,
    )
    return deposited


def test_group5_real_teller_convert_and_withdraw_conserves_after_rate_change(
    stability_pool,
    teller,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    createDebtTerms,
):
    """Never-skip #1: real Teller sGREEN route with temporal rate change."""
    _configure_launch_sgreen(
        savings_green,
        setGeneralConfig,
        setAssetConfig,
        createDebtTerms,
    )
    deposit_green = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, deposit_green, sender=whale)
    deposited_sgreen = _convert_and_deposit(
        teller,
        green_token,
        bob,
        deposit_green,
    )
    clear_transient_storage()

    stab_shares_before = stability_pool.userBalances(bob, savings_green)
    pool_sgreen_before = savings_green.balanceOf(stability_pool)
    assert deposited_sgreen == pool_sgreen_before
    assert stab_shares_before != 0

    # Move the ERC-4626 rate between modeled transactions without changing the
    # Stability Pool's sGREEN custody or internal share count.
    rate_donation = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(savings_green, rate_donation, sender=whale)
    pool_green_value_before = savings_green.convertToAssets(pool_sgreen_before)
    assert pool_green_value_before == deposit_green + rate_donation

    bob_sgreen_before = savings_green.balanceOf(bob)
    withdrawn = teller.withdraw(
        savings_green,
        MAX_UINT256,
        bob,
        stability_pool,
        1,
        sender=bob,
    )

    pool_sgreen_after = savings_green.balanceOf(stability_pool)
    delivered_sgreen = savings_green.balanceOf(bob) - bob_sgreen_before
    teller_event = filter_logs(teller, "TellerWithdrawal")[0]
    clear_transient_storage()

    assert withdrawn == delivered_sgreen
    assert pool_sgreen_before - pool_sgreen_after == delivered_sgreen
    assert teller_event.amount == withdrawn
    assert teller_event.isDepleted
    assert stability_pool.userBalances(bob, savings_green) == 0
    assert stability_pool.totalBalances(savings_green) == 0

    delivered_green_value = savings_green.convertToAssets(delivered_sgreen)
    residual_green_value = savings_green.convertToAssets(pool_sgreen_after)
    assert abs(
        pool_green_value_before - delivered_green_value - residual_green_value
    ) <= 1


def test_group5_normal_second_convert_mints_nonzero_stab_shares(
    stability_pool,
    teller,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    createDebtTerms,
):
    """Adjacent control disproving the initial normal-cohort zero-share theory."""
    _configure_launch_sgreen(
        savings_green,
        setGeneralConfig,
        setAssetConfig,
        createDebtTerms,
    )
    first_deposit = 5_000_000 * EIGHTEEN_DECIMALS
    assert _convert_and_deposit(
        teller,
        green_token,
        whale,
        first_deposit,
    ) == first_deposit
    clear_transient_storage()

    green_token.transfer(bob, LAUNCH_MIN_SGREEN_DEPOSIT, sender=whale)
    bob_shares_before = stability_pool.userBalances(bob, savings_green)
    deposited = _convert_and_deposit(
        teller,
        green_token,
        bob,
        LAUNCH_MIN_SGREEN_DEPOSIT,
    )
    minted = stability_pool.userBalances(bob, savings_green) - bob_shares_before

    assert deposited == LAUNCH_MIN_SGREEN_DEPOSIT
    assert minted > 0
    event = filter_logs(teller, "TellerDeposit")[0]
    clear_transient_storage()
    assert event.user == bob
    assert event.amount == deposited
    assert event.asset == savings_green.address
    assert event.vaultAddr == stability_pool.address


def test_group5_deposit_guards_revert_before_teller_custody_commits(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    green_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #1: invalid stab deposits roll back Teller's prior transfer."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token, [1])
    setAssetConfig(charlie_token, [1])
    setAssetConfig(green_token, [1])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    with boa.reverts("cannot deposit 0"):
        teller.deposit(alpha_token, 0, bob, stability_pool, vault_id, sender=bob)

    green_amount = EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    pool_green_before = green_token.balanceOf(stability_pool)
    alice_green_before = green_token.balanceOf(alice)
    # Teller intentionally collapses a target-vault revert into its external
    # deposit assertion, so prove the user-flow rollback rather than its inner
    # dev string.
    with boa.reverts():
        teller.deposit(
            green_token,
            green_amount,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        )
    assert green_token.balanceOf(stability_pool) == pool_green_before
    assert green_token.balanceOf(alice) == alice_green_before
    assert stability_pool.indexOfAsset(green_token) == 0

    stab_deposit = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, stab_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, stab_deposit, sender=bob)
    assert teller.deposit(
        bravo_token, stab_deposit, bob, stability_pool, vault_id, sender=bob
    ) == stab_deposit
    clear_transient_storage()

    reserved_alpha = EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, reserved_alpha, sender=alpha_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token,
        EIGHTEEN_DECIMALS,
        alpha_token,
        reserved_alpha,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.totalClaimableBalances(alpha_token) == reserved_alpha
    alpha_token.transfer(alice, reserved_alpha, sender=alpha_token_whale)
    alpha_token.approve(teller, reserved_alpha, sender=alice)
    pool_alpha_before = alpha_token.balanceOf(stability_pool)
    alice_alpha_before = alpha_token.balanceOf(alice)
    with boa.reverts():
        teller.deposit(
            alpha_token,
            reserved_alpha,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        )
    assert alpha_token.balanceOf(stability_pool) == pool_alpha_before
    assert alpha_token.balanceOf(alice) == alice_alpha_before
    assert stability_pool.totalClaimableBalances(alpha_token) == reserved_alpha

    unpriced_amount = 10**charlie_token.decimals()
    charlie_token.transfer(alice, unpriced_amount, sender=charlie_token_whale)
    charlie_token.approve(teller, unpriced_amount, sender=alice)
    pool_charlie_before = charlie_token.balanceOf(stability_pool)
    with boa.reverts():
        teller.deposit(
            charlie_token,
            unpriced_amount,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        )
    assert charlie_token.balanceOf(stability_pool) == pool_charlie_before
    assert charlie_token.balanceOf(alice) == unpriced_amount


def test_group5_new_depositor_must_not_capture_abandoned_dormant_value(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Never-skip #2: press the post-zero-share dormant ownership boundary."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(alpha_token, [1])
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    original_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, original_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, original_deposit, sender=bob)
    assert teller.deposit(
        alpha_token,
        original_deposit,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit
    clear_transient_storage()

    dormant = ACTIVATION_THRESHOLD - 1
    bravo_token.transfer(stability_pool, dormant, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        dormant,
        bravo_token,
        dormant,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1

    assert teller.withdraw(
        alpha_token,
        MAX_UINT256,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit - dormant
    clear_transient_storage()
    assert stability_pool.totalBalances(alpha_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == dormant
    # The exited holder has no remaining shares and cannot recover this
    # recorded liability before a replacement cohort arrives.
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            sender=bob,
        )

    replacement_deposit = EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, replacement_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, replacement_deposit, sender=alice)
    assert teller.deposit(
        alpha_token,
        replacement_deposit,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    ) == replacement_deposit
    clear_transient_storage()
    alice_value_before = stability_pool.getTotalUserValue(alice, alpha_token)
    assert alice_value_before == replacement_deposit
    alice_alpha_before = alpha_token.balanceOf(alice)
    alice_bravo_before = bravo_token.balanceOf(alice)

    claimed_usd = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        bravo_token,
        sender=alice,
    )
    clear_transient_storage()
    delivered = bravo_token.balanceOf(alice) - alice_bravo_before
    assert delivered == dormant
    assert claimed_usd == dormant
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0

    recovered_amount = teller.withdraw(
        alpha_token,
        MAX_UINT256,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    )
    recovered_alpha = alpha_token.balanceOf(alice) - alice_alpha_before
    assert recovered_amount == recovered_alpha
    captured_value = recovered_alpha + delivered - replacement_deposit
    assert captured_value <= 1
    assert stability_pool.totalBalances(alpha_token) == 0


def test_group5_appreciated_dormant_value_cannot_be_captured_after_zero_share_exit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Dormant state must not let a later sole cohort acquire appreciated custody."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    original_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, original_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, original_deposit, sender=bob)
    assert teller.deposit(
        alpha_token,
        original_deposit,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit
    clear_transient_storage()

    dormant = ACTIVATION_THRESHOLD - 1
    bravo_token.transfer(stability_pool, dormant, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        dormant,
        bravo_token,
        dormant,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert teller.withdraw(
        alpha_token,
        MAX_UINT256,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit - dormant
    clear_transient_storage()
    assert stability_pool.totalBalances(alpha_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1

    appreciated_price = 1_000 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, appreciated_price)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1
    assert stability_pool.getTotalValue(alpha_token) == 0

    replacement_deposit = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, replacement_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, replacement_deposit, sender=alice)
    assert teller.deposit(
        alpha_token,
        replacement_deposit,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    ) == replacement_deposit
    clear_transient_storage()
    alice_value_before = stability_pool.getTotalUserValue(alice, alpha_token)
    assert alice_value_before == replacement_deposit
    alpha_before = alpha_token.balanceOf(alice)
    bravo_before = bravo_token.balanceOf(alice)

    claimed_usd = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        bravo_token,
        sender=alice,
    )
    clear_transient_storage()
    delivered = bravo_token.balanceOf(alice) - bravo_before
    delivered_value = delivered * appreciated_price // EIGHTEEN_DECIMALS
    assert delivered == dormant
    assert claimed_usd == delivered_value

    recovered = teller.withdraw(
        alpha_token,
        MAX_UINT256,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    )
    assert recovered == alpha_token.balanceOf(alice) - alpha_before
    captured_value = recovered + delivered_value - replacement_deposit
    assert captured_value <= 1


def test_group5_active_post_exit_claim_is_priced_into_new_depositor_shares(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Adjacent control: activation makes an appreciated inherited claim enter NAV."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(alpha_token, [1])
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    vault_id = vault_book.getRegId(stability_pool)
    original_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, original_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, original_deposit, sender=bob)
    assert teller.deposit(
        alpha_token,
        original_deposit,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit
    clear_transient_storage()
    dormant = ACTIVATION_THRESHOLD - 1
    bravo_token.transfer(stability_pool, dormant, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        dormant,
        bravo_token,
        dormant,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert teller.withdraw(
        alpha_token,
        MAX_UINT256,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_deposit - dormant

    # The same custody becomes active only after the separate paused
    # maintenance action; this isolates capture prevention, not recovery.
    appreciated_price = 1_000 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, appreciated_price)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 2

    replacement_deposit = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, replacement_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, replacement_deposit, sender=alice)
    assert teller.deposit(
        alpha_token,
        replacement_deposit,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    ) == replacement_deposit
    clear_transient_storage()
    alice_value_before = stability_pool.getTotalUserValue(alice, alpha_token)
    alice_alpha_before = alpha_token.balanceOf(alice)
    alice_bravo_before = bravo_token.balanceOf(alice)

    claimed_usd = claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=alice
    )
    clear_transient_storage()
    delivered = bravo_token.balanceOf(alice) - alice_bravo_before
    withdrawn = teller.withdraw(
        alpha_token,
        MAX_UINT256,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    )
    recovered_alpha = alpha_token.balanceOf(alice) - alice_alpha_before
    assert withdrawn == recovered_alpha

    delivered_value = delivered * appreciated_price // EIGHTEEN_DECIMALS
    # Claim sizing floors in claim-asset units, so its internal USD report can
    # differ from independently priced delivery by less than one raw bravo unit.
    assert abs(claimed_usd - delivered_value) <= appreciated_price // EIGHTEEN_DECIMALS
    assert (
        abs(
            recovered_alpha
            + delivered_value
            - alice_value_before
        )
        <= appreciated_price // EIGHTEEN_DECIMALS
    )
    assert (
        abs(recovered_alpha + delivered_value - replacement_deposit)
        <= appreciated_price // EIGHTEEN_DECIMALS
    )
    # Activation prevents Alice from extracting the inherited value, but the
    # virtual-share root leaves that value as an unowned alpha seed once she
    # exits. This is the separately accepted empty-supply containment issue,
    # not a cure for the former holder's recovery.
    assert stability_pool.userBalances(alice, alpha_token) == 0
    assert stability_pool.totalBalances(alpha_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert alpha_token.balanceOf(stability_pool) == 100 * EIGHTEEN_DECIMALS


def test_group5_launch_sgreen_new_depositor_cannot_capture_dormant_value(
    stability_pool,
    teller,
    green_token,
    savings_green,
    bravo_token,
    bravo_token_whale,
    whale,
    bob,
    alice,
    auction_house,
    mock_price_source,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
):
    """Launch-profile reproduction of the zero-share dormant capture boundary."""
    _configure_launch_sgreen(
        savings_green,
        setGeneralConfig,
        setAssetConfig,
        createDebtTerms,
    )
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    original_green = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, original_green, sender=whale)
    assert _convert_and_deposit(teller, green_token, bob, original_green) == original_green
    clear_transient_storage()

    dormant = ACTIVATION_THRESHOLD - 1
    bravo_token.transfer(stability_pool, dormant, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green,
        dormant,
        bravo_token,
        dormant,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.getClaimAssetState(savings_green, bravo_token) == 1
    assert teller.withdraw(
        savings_green,
        MAX_UINT256,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == original_green - dormant
    clear_transient_storage()
    assert stability_pool.totalBalances(savings_green) == 0
    assert stability_pool.claimableBalances(savings_green, bravo_token) == dormant

    replacement_green = EIGHTEEN_DECIMALS
    green_token.transfer(alice, replacement_green, sender=whale)
    assert _convert_and_deposit(teller, green_token, alice, replacement_green) == replacement_green
    clear_transient_storage()
    alice_value_before = stability_pool.getTotalUserValue(alice, savings_green)
    assert alice_value_before == replacement_green
    alice_sgreen_before = savings_green.balanceOf(alice)
    alice_bravo_before = bravo_token.balanceOf(alice)

    claimed_usd = claim_from_stability_pool(
        teller,
        vault_id,
        savings_green,
        bravo_token,
        sender=alice,
    )
    clear_transient_storage()
    delivered = bravo_token.balanceOf(alice) - alice_bravo_before
    assert claimed_usd == dormant
    assert delivered == dormant

    recovered_sgreen = teller.withdraw(
        savings_green,
        MAX_UINT256,
        alice,
        stability_pool,
        vault_id,
        sender=alice,
    )
    recovered_green_value = savings_green.convertToAssets(recovered_sgreen)
    assert recovered_sgreen == savings_green.balanceOf(alice) - alice_sgreen_before
    captured_value = recovered_green_value + delivered - replacement_green
    assert captured_value <= 1


def test_group5_claim_auto_deposit_to_second_pool_must_not_commit_zero_shares(
    stability_pool,
    alternate_stability_pool,
    registerVault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """A claim auto-deposit into a second pool must not commit zero shares.

    The nested `depositFromTrusted` used to move one raw Bravo into the
    target with zero target shares. The parent claim must now revert
    `cannot mint 0 shares` and leave pre-claim state unchanged.
    """
    target_vault_id = registerVault(
        alternate_stability_pool,
        "Group 5 auto-deposit target Stability Pool",
    )
    source_vault_id = vault_book.getRegId(stability_pool)
    setGeneralConfig()
    setAssetConfig(alpha_token, [source_vault_id])
    setAssetConfig(bravo_token, [target_vault_id])
    setAssetConfig(charlie_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)

    # Build the target's adjacent two-raw-unit boundary: it holds a normal
    # active claim that later appreciates, while Bravo remains its stab asset.
    target_deposit = 2 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, target_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, target_deposit, sender=bob)
    assert teller.deposit(
        bravo_token,
        target_deposit,
        bob,
        alternate_stability_pool,
        target_vault_id,
        sender=bob,
    ) == target_deposit
    clear_transient_storage()
    active_claim = 10**charlie_token.decimals()
    charlie_token.transfer(
        alternate_stability_pool,
        active_claim,
        sender=charlie_token_whale,
    )
    alternate_stability_pool.swapForLiquidatedCollateral(
        bravo_token,
        EIGHTEEN_DECIMALS,
        charlie_token,
        active_claim,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    clear_transient_storage()
    assert (
        alternate_stability_pool.getClaimAssetState(bravo_token, charlie_token)
        == 2
    )
    mock_price_source.setPrice(charlie_token, 200_000_000 * EIGHTEEN_DECIMALS)

    # Adjacent safe branch: the same target mints one share for two raw Bravo
    # units, so the one-unit callback below is at the intended threshold.
    with boa.env.anchor():
        bravo_token.transfer(alice, 2, sender=bravo_token_whale)
        bravo_token.approve(teller, 2, sender=alice)
        assert teller.deposit(
            bravo_token,
            2,
            alice,
            alternate_stability_pool,
            target_vault_id,
            sender=alice,
        ) == 2
        assert alternate_stability_pool.userBalances(alice, bravo_token) == 1
    clear_transient_storage()

    # Source pool holds one raw, dormant Bravo claim. Auto-deposit resolves its
    # first vault id to the *other* Stability Pool and invokes
    # Teller.depositFromTrusted from the claim callback.
    source_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, source_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, source_deposit, sender=alice)
    assert teller.deposit(
        alpha_token,
        source_deposit,
        alice,
        stability_pool,
        source_vault_id,
        sender=alice,
    ) == source_deposit
    clear_transient_storage()
    bravo_token.transfer(stability_pool, 1, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        1,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    clear_transient_storage()
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1

    source_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    source_claim_custody = bravo_token.balanceOf(stability_pool)
    source_shares = stability_pool.userBalances(alice, alpha_token)
    source_unreserved = (
        alpha_token.balanceOf(stability_pool)
        - stability_pool.totalClaimableBalances(alpha_token)
    )
    target_custody = bravo_token.balanceOf(alternate_stability_pool)
    target_shares = alternate_stability_pool.userBalances(alice, bravo_token)
    alice_bravo = bravo_token.balanceOf(alice)
    bob_bravo = bravo_token.balanceOf(bob)
    with pytest.raises(BoaError) as exc_info:
        claim_from_stability_pool(
            teller,
            source_vault_id,
            alpha_token,
            bravo_token,
            user=alice,
            should_auto_deposit=True,
            sender=alice,
        )
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == source_claimable
    assert bravo_token.balanceOf(stability_pool) == source_claim_custody
    assert stability_pool.userBalances(alice, alpha_token) == source_shares
    assert (
        alpha_token.balanceOf(stability_pool)
        - stability_pool.totalClaimableBalances(alpha_token)
        == source_unreserved
    )
    assert bravo_token.balanceOf(alternate_stability_pool) == target_custody
    assert alternate_stability_pool.userBalances(alice, bravo_token) == 0
    assert alternate_stability_pool.userBalances(alice, bravo_token) == target_shares
    assert bravo_token.balanceOf(alice) == alice_bravo
    assert bravo_token.balanceOf(bob) == bob_bravo


def test_group5_redeem_does_not_spend_preexisting_reserved_green(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    whale,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #3: payer payment P remains separate from reserved GREEN B."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    stab_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, stab_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, stab_deposit, sender=teller.address
    )

    reserved_green = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(stability_pool, reserved_green, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        green_token,
        reserved_green,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    redeemable_bravo = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, redeemable_bravo, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        redeemable_bravo,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.totalClaimableBalances(green_token) == reserved_green

    green_token.transfer(bob, redeemable_bravo, sender=whale)
    green_token.approve(teller, redeemable_bravo, sender=bob)
    vault_id = vault_book.getRegId(stability_pool)
    green_spent = redeem_from_stability_pool(
        teller,
        vault_id,
        bravo_token,
        redeemable_bravo,
        bob,
        sender=bob,
    )
    clear_transient_storage()

    assert green_spent == redeemable_bravo
    assert bravo_token.balanceOf(bob) == redeemable_bravo
    assert green_token.balanceOf(stability_pool) == reserved_green + redeemable_bravo
    assert stability_pool.claimableBalances(
        alpha_token, green_token
    ) == reserved_green + redeemable_bravo
    assert stability_pool.totalClaimableBalances(
        green_token
    ) == reserved_green + redeemable_bravo


def test_group5_fifteen_redemption_rows_preserve_each_payment_replacement(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    whale,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #3/#5: 15 repeated redeem rows consume only paid GREEN."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit, sender=teller.address
    )
    claimable = 90 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        EIGHTEEN_DECIMALS,
        bravo_token,
        claimable,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    value_before = stability_pool.getTotalUserValue(bob, alpha_token)
    row_payment = 4 * EIGHTEEN_DECIMALS
    total_payment = 15 * row_payment
    green_token.transfer(bob, total_payment, sender=whale)
    green_token.approve(teller, total_payment, sender=bob)
    redemptions = [(bravo_token.address, row_payment) for _ in range(15)]
    bravo_before = bravo_token.balanceOf(bob)

    green_spent = teller.redeemManyFromStabilityPool(
        vault_id,
        redemptions,
        total_payment,
        bob,
        False,
        False,
        True,
        sender=bob,
    )

    delivered = bravo_token.balanceOf(bob) - bravo_before
    assert green_spent == total_payment
    assert delivered == total_payment
    assert green_token.balanceOf(stability_pool) == total_payment
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == (
        claimable - delivered
    )
    assert stability_pool.claimableBalances(alpha_token, green_token) == total_payment
    assert stability_pool.totalClaimableBalances(green_token) == total_payment
    assert stability_pool.getTotalUserValue(bob, alpha_token) == value_before


def test_group5_nonzero_stab_deposit_must_not_commit_zero_shares(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #1: the zero-share boundary must revert before custody moves."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    initial_deposit = 2 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, initial_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, initial_deposit, sender=bob)
    assert teller.deposit(
        alpha_token,
        initial_deposit,
        bob,
        stability_pool,
        vault_id,
        sender=bob,
    ) == initial_deposit
    clear_transient_storage()

    # A normally admitted active claim can later appreciate. With 2e26 initial
    # stab shares, a one-token claim repriced to $200m makes a one-unit alpha
    # deposit round down to zero shares; two units mint one.
    active_claim = EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, active_claim, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        EIGHTEEN_DECIMALS,
        bravo_token,
        active_claim,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    clear_transient_storage()
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 2
    mock_price_source.setPrice(bravo_token, 200_000_000 * EIGHTEEN_DECIMALS)

    with boa.env.anchor():
        alpha_token.transfer(alice, 2, sender=alpha_token_whale)
        alpha_token.approve(teller, 2, sender=alice)
        assert teller.deposit(
            alpha_token,
            2,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        ) == 2
        assert stability_pool.userBalances(alice, alpha_token) == 1
    clear_transient_storage()

    zero_share_deposit = 1
    alpha_token.transfer(alice, zero_share_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, zero_share_deposit, sender=alice)
    pool_before = alpha_token.balanceOf(stability_pool)
    alice_before = alpha_token.balanceOf(alice)
    shares_before = stability_pool.userBalances(alice, alpha_token)
    with pytest.raises(BoaError) as exc_info:
        teller.deposit(
            alpha_token,
            zero_share_deposit,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        )
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()

    assert alpha_token.balanceOf(stability_pool) == pool_before
    assert alpha_token.balanceOf(alice) == alice_before
    assert stability_pool.userBalances(alice, alpha_token) == shares_before


def test_group5_launch_sgreen_qualified_topup_must_not_commit_zero_shares(
    stability_pool,
    teller,
    green_token,
    savings_green,
    bravo_token,
    bravo_token_whale,
    whale,
    bob,
    alice,
    auction_house,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
    createDebtTerms,
):
    """A launch-profile 1-wei top-up below the share threshold must revert.

    After a qualified min deposit and a $200M active-claim reprice, a
    1-wei convert used to add custody with no new shares. It must now
    revert `cannot mint 0 shares`.
    """
    _configure_launch_sgreen(
        savings_green,
        setGeneralConfig,
        setAssetConfig,
        createDebtTerms,
    )
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    initial_green = 2 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, initial_green, sender=whale)
    assert _convert_and_deposit(teller, green_token, bob, initial_green) == initial_green
    clear_transient_storage()

    bravo_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green,
        EIGHTEEN_DECIMALS,
        bravo_token,
        EIGHTEEN_DECIMALS,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    clear_transient_storage()
    assert stability_pool.getClaimAssetState(savings_green, bravo_token) == 2
    mock_price_source.setPrice(bravo_token, 200_000_000 * EIGHTEEN_DECIMALS)

    # Alice first clears the planned $0.01 minimum, so the next transaction is
    # an ordinary existing-position top-up rather than a rejected first entry.
    green_token.transfer(alice, LAUNCH_MIN_SGREEN_DEPOSIT, sender=whale)
    assert _convert_and_deposit(
        teller, green_token, alice, LAUNCH_MIN_SGREEN_DEPOSIT
    ) == LAUNCH_MIN_SGREEN_DEPOSIT
    clear_transient_storage()
    alice_shares_before = stability_pool.userBalances(alice, savings_green)
    assert alice_shares_before != 0

    with boa.env.anchor():
        green_token.transfer(alice, 2, sender=whale)
        green_token.approve(teller, 2, sender=alice)
        assert _convert_and_deposit(teller, green_token, alice, 2) == 2
        assert stability_pool.userBalances(alice, savings_green) == (
            alice_shares_before + 1
        )
    clear_transient_storage()

    green_token.transfer(alice, 1, sender=whale)
    green_token.approve(teller, 1, sender=alice)
    pool_before = savings_green.balanceOf(stability_pool)
    alice_green_before = green_token.balanceOf(alice)
    with pytest.raises(BoaError) as exc_info:
        _convert_and_deposit(teller, green_token, alice, 1)
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()

    assert savings_green.balanceOf(stability_pool) == pool_before
    assert green_token.balanceOf(alice) == alice_green_before
    assert stability_pool.userBalances(alice, savings_green) == alice_shares_before


def test_group5_teller_withdraw_boundaries_preserve_active_claim_ownership(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Never-skip #1: Teller follows each holder's active-NAV withdrawal branch."""
    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(alpha_token, [1])
        setAssetConfig(bravo_token)
        setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        vault_id = vault_book.getRegId(stability_pool)

        for user in (bob, alice):
            alpha_token.transfer(user, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
            alpha_token.approve(teller, 100 * EIGHTEEN_DECIMALS, sender=user)
            assert teller.deposit(
                alpha_token,
                100 * EIGHTEEN_DECIMALS,
                user,
                stability_pool,
                vault_id,
                sender=user,
            ) == 100 * EIGHTEEN_DECIMALS
            clear_transient_storage()

        bravo_token.transfer(stability_pool, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            100 * EIGHTEEN_DECIMALS,
            bravo_token,
            100 * EIGHTEEN_DECIMALS,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        )
        assert stability_pool.getTotalAmountForUser(alice, alpha_token) == (
            100 * EIGHTEEN_DECIMALS
        )
        with boa.reverts("cannot withdraw 0"):
            teller.withdraw(alpha_token, 0, alice, stability_pool, vault_id, sender=alice)

        boa.env.time_travel(blocks=1)
        alice_alpha_before = alpha_token.balanceOf(alice)
        assert teller.withdraw(
            alpha_token,
            MAX_UINT256,
            alice,
            stability_pool,
            vault_id,
            sender=alice,
        ) == 100 * EIGHTEEN_DECIMALS
        assert alpha_token.balanceOf(alice) - alice_alpha_before == 100 * EIGHTEEN_DECIMALS
        assert stability_pool.userBalances(alice, alpha_token) == 0
        assert stability_pool.totalBalances(alpha_token) == stability_pool.userBalances(
            bob, alpha_token
        )
        assert alpha_token.balanceOf(stability_pool) == 0
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == (
            100 * EIGHTEEN_DECIMALS
        )

        bob_bravo_before = bravo_token.balanceOf(bob)
        assert claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        ) == 100 * EIGHTEEN_DECIMALS
        clear_transient_storage()
        assert bravo_token.balanceOf(bob) - bob_bravo_before == 100 * EIGHTEEN_DECIMALS
        assert stability_pool.totalBalances(alpha_token) == 0

    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(alpha_token, [1])
        setAssetConfig(bravo_token)
        setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        vault_id = vault_book.getRegId(stability_pool)

        alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        alpha_token.approve(teller, 100 * EIGHTEEN_DECIMALS, sender=bob)
        assert teller.deposit(
            alpha_token,
            100 * EIGHTEEN_DECIMALS,
            bob,
            stability_pool,
            vault_id,
            sender=bob,
        ) == 100 * EIGHTEEN_DECIMALS
        clear_transient_storage()
        bravo_token.transfer(stability_pool, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            EIGHTEEN_DECIMALS,
            bravo_token,
            200 * EIGHTEEN_DECIMALS,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        )
        shares_before = stability_pool.userBalances(bob, alpha_token)
        assert stability_pool.getTotalAmountForUser(bob, alpha_token) > alpha_token.balanceOf(
            stability_pool
        )

        boa.env.time_travel(blocks=1)
        assert teller.withdraw(
            alpha_token,
            MAX_UINT256,
            bob,
            stability_pool,
            vault_id,
            sender=bob,
        ) == 99 * EIGHTEEN_DECIMALS
        assert alpha_token.balanceOf(stability_pool) == 0
        assert 0 < stability_pool.userBalances(bob, alpha_token) < shares_before
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == (
            200 * EIGHTEEN_DECIMALS
        )
    clear_transient_storage()


def test_group5_stab_deposit_many_and_duplicate_withdraw_many_are_atomic(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #6: real stab batches, including the duplicate exit rollback."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    first = 3 * EIGHTEEN_DECIMALS
    second = 2 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, first + second, sender=alpha_token_whale)
    alpha_token.approve(teller, first + second, sender=bob)
    rows = [
        (alpha_token.address, first, stability_pool.address, 1),
        (alpha_token.address, second, stability_pool.address, 1),
    ]
    assert teller.depositMany(bob, rows, sender=bob) == 2
    deposit_logs = filter_logs(teller, "TellerDeposit")
    assert len(deposit_logs) == 2
    assert [log.amount for log in deposit_logs] == [first, second]
    assert alpha_token.balanceOf(stability_pool) == first + second
    shares_before = stability_pool.userBalances(bob, alpha_token)
    custody_before = alpha_token.balanceOf(stability_pool)
    clear_transient_storage()
    boa.env.time_travel(blocks=1)

    duplicate_full_exit = (
        alpha_token.address,
        MAX_UINT256,
        stability_pool.address,
        1,
    )
    with boa.reverts():
        teller.withdrawMany(bob, [duplicate_full_exit, duplicate_full_exit], sender=bob)

    assert stability_pool.userBalances(bob, alpha_token) == shares_before
    assert stability_pool.totalBalances(alpha_token) == shares_before
    assert alpha_token.balanceOf(stability_pool) == custody_before
    assert alpha_token.balanceOf(bob) == 0
    assert filter_logs(teller, "TellerWithdrawal") == []


def test_group5_stab_deposit_and_withdraw_many_at_twenty_row_ceiling(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #6: all 20 stab rows commit and settle independently."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)
    row_amount = EIGHTEEN_DECIMALS
    total_amount = 20 * row_amount
    alpha_token.transfer(bob, total_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, total_amount, sender=bob)
    deposits = [
        (alpha_token.address, row_amount, stability_pool.address, vault_id)
        for _ in range(20)
    ]
    assert teller.depositMany(bob, deposits, sender=bob) == 20
    assert len(filter_logs(teller, "TellerDeposit")) == 20
    assert alpha_token.balanceOf(stability_pool) == total_amount
    assert stability_pool.userBalances(bob, alpha_token) > 0
    clear_transient_storage()
    boa.env.time_travel(blocks=1)

    withdrawals = [
        (alpha_token.address, row_amount, stability_pool.address, vault_id)
        for _ in range(20)
    ]
    assert teller.withdrawMany(bob, withdrawals, sender=bob) == 20
    assert len(filter_logs(teller, "TellerWithdrawal")) == 20
    assert alpha_token.balanceOf(stability_pool) == 0
    assert alpha_token.balanceOf(bob) == total_amount
    assert stability_pool.userBalances(bob, alpha_token) == 0
    assert stability_pool.totalBalances(alpha_token) == 0


def test_group5_teller_path_authorization_is_entry_specific(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    green_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    setUserConfig,
):
    """Never-skip #4: the four Teller gates are intentionally distinct."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    setUserConfig(bob, _canAnyoneDeposit=False)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    deposited = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposited, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposited, sender=teller.address
    )
    claimable = EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        claimable,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    vault_id = vault_book.getRegId(stability_pool)

    alpha_token.transfer(alice, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(teller, EIGHTEEN_DECIMALS, sender=alice)
    with boa.reverts("cannot deposit for user"):
        teller.deposit(
            alpha_token,
            EIGHTEEN_DECIMALS,
            bob,
            stability_pool,
            vault_id,
            sender=alice,
        )
    with boa.reverts("not allowed to withdraw for user"):
        teller.withdraw(
            alpha_token,
            EIGHTEEN_DECIMALS,
            bob,
            stability_pool,
            vault_id,
            sender=alice,
        )
    with boa.reverts("cannot claim for user"):
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            user=bob,
            sender=alice,
        )

    green_token.transfer(alice, claimable, sender=whale)
    green_token.approve(teller, claimable, sender=alice)
    with boa.reverts("not allowed to deposit for user"):
        redeem_from_stability_pool(
            teller,
            vault_id,
            bravo_token,
            claimable,
            recipient=bob,
            sender=alice,
        )

    # The ordinary self-claim remains live after every rejected helper route.
    assert claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=bob
    ) == claimable


def test_group5_third_party_convert_still_requires_target_deposit_permission(
    stability_pool,
    teller,
    green_token,
    savings_green,
    whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    createDebtTerms,
    setUserConfig,
):
    """Never-skip #4: convert's internal deposit does not bypass third-party auth."""
    _configure_launch_sgreen(
        savings_green,
        setGeneralConfig,
        setAssetConfig,
        createDebtTerms,
    )
    setUserConfig(bob, _canAnyoneDeposit=False)
    green_amount = EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    alice_green_before = green_token.balanceOf(alice)
    pool_sgreen_before = savings_green.balanceOf(stability_pool)

    with boa.reverts("cannot deposit for user"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(
            bob, green_amount, sender=alice
        )

    assert green_token.balanceOf(alice) == alice_green_before
    assert savings_green.balanceOf(stability_pool) == pool_sgreen_before
    assert stability_pool.userBalances(bob, savings_green) == 0


def test_group5_claim_config_soft_skips_before_third_party_auth(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Never-skip #4/#5: config soft-skip precedes the later auth assert."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token, _canClaimInStabPool=False)
    setAssetConfig(charlie_token)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    deposit = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, deposit, sender=bob)
    assert teller.deposit(
        alpha_token, deposit, bob, stability_pool, vault_id, sender=bob
    ) == deposit
    clear_transient_storage()

    disabled_claim = 2 * EIGHTEEN_DECIMALS
    enabled_claim = 2 * 10**charlie_token.decimals()
    bravo_token.transfer(stability_pool, disabled_claim, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        disabled_claim,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    charlie_token.transfer(stability_pool, enabled_claim, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        charlie_token,
        enabled_claim,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )

    disabled_row = [(alpha_token.address, bravo_token.address, MAX_UINT256)]
    mixed_rows = disabled_row + [
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]
    with boa.env.anchor():
        with boa.reverts("nothing claimed"):
            teller.claimManyFromStabilityPool(
                vault_id, disabled_row, bob, False, sender=alice
            )

    before = (
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.claimableBalances(alpha_token, charlie_token),
        bravo_token.balanceOf(alice),
        charlie_token.balanceOf(alice),
    )
    with boa.reverts("cannot claim for user"):
        teller.claimManyFromStabilityPool(
            vault_id, mixed_rows, bob, False, sender=alice
        )
    assert (
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.claimableBalances(alpha_token, charlie_token),
        bravo_token.balanceOf(alice),
        charlie_token.balanceOf(alice),
    ) == before

    claimed_usd = teller.claimManyFromStabilityPool(
        vault_id, mixed_rows, bob, False, sender=bob
    )
    delivered_usd = enabled_claim * EIGHTEEN_DECIMALS // 10**charlie_token.decimals()
    assert claimed_usd >= delivered_usd
    assert claimed_usd - delivered_usd < EIGHTEEN_DECIMALS // 10**charlie_token.decimals()
    assert bravo_token.balanceOf(bob) == 0
    assert charlie_token.balanceOf(bob) == enabled_claim
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == disabled_claim
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == 0


def test_group5_fifteen_partial_claim_rows_preserve_reserves_and_value(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Never-skip #2/#5: duplicated partial rows at the claim ceiling stay bounded."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, deposit, sender=bob)
    assert teller.deposit(
        alpha_token, deposit, bob, stability_pool, vault_id, sender=bob
    ) == deposit
    clear_transient_storage()

    claimable = 90 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        EIGHTEEN_DECIMALS,
        bravo_token,
        claimable,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    value_before = stability_pool.getTotalUserValue(bob, alpha_token)
    shares_before = stability_pool.userBalances(bob, alpha_token)
    custody_before = bravo_token.balanceOf(stability_pool)
    liability_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    bob_before = bravo_token.balanceOf(bob)

    row_max_usd = 4 * EIGHTEEN_DECIMALS
    claims = [
        (alpha_token.address, bravo_token.address, row_max_usd) for _ in range(15)
    ]
    claimed_usd = teller.claimManyFromStabilityPool(
        vault_id, claims, bob, False, sender=bob
    )
    clear_transient_storage()

    delivered = bravo_token.balanceOf(bob) - bob_before
    value_after = stability_pool.getTotalUserValue(bob, alpha_token)
    assert delivered == 15 * row_max_usd
    assert claimed_usd >= delivered
    assert claimed_usd - delivered <= 15
    assert custody_before - bravo_token.balanceOf(stability_pool) == delivered
    assert liability_before - stability_pool.claimableBalances(
        alpha_token, bravo_token
    ) == delivered
    assert stability_pool.totalClaimableBalances(bravo_token) == claimable - delivered
    assert shares_before > stability_pool.userBalances(bob, alpha_token) > 0
    assert abs(value_before - value_after - delivered) <= 15


def test_group5_overflowing_reward_rate_reverts_claim_atomically(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """An unchecked governance reward rate may freeze claims but cannot half-settle one."""
    setGeneralConfig()
    setAssetConfig(alpha_token, [1])
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=MAX_UINT256)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    deposited = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposited, sender=alpha_token_whale)
    alpha_token.approve(teller, deposited, sender=bob)
    assert teller.deposit(
        alpha_token, deposited, bob, stability_pool, vault_id, sender=bob
    ) == deposited
    clear_transient_storage()
    claimable = EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        EIGHTEEN_DECIMALS,
        bravo_token,
        claimable,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    before = (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        bravo_token.balanceOf(stability_pool),
        bravo_token.balanceOf(bob),
    )

    with boa.reverts():
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        )

    assert (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        bravo_token.balanceOf(stability_pool),
        bravo_token.balanceOf(bob),
    ) == before


def test_group5_sgreen_payment_uses_share_input_and_green_settlement_at_nonunit_rate(
    stability_pool,
    savings_green,
    green_token,
    bravo_token,
    bravo_token_whale,
    alice,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """Never-skip #3: sGREEN input units, GREEN settlement, and replacement."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    seed_green = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, seed_green, sender=whale)
    green_token.approve(savings_green, seed_green, sender=alice)
    seed_shares = savings_green.deposit(seed_green, stability_pool, sender=alice)
    stability_pool.depositTokensInVault(
        alice, savings_green, seed_shares, sender=teller.address
    )

    # Make each sGREEN share worth two GREEN before the payer acquires shares.
    green_token.transfer(savings_green, seed_green, sender=whale)
    assert savings_green.convertToAssets(EIGHTEEN_DECIMALS) == 2 * EIGHTEEN_DECIMALS
    claimable = 20 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green,
        1,
        bravo_token,
        claimable,
        alice,
        green_token,
        savings_green,
        sender=auction_house.address,
    )

    green_token.transfer(bob, claimable, sender=whale)
    green_token.approve(savings_green, claimable, sender=bob)
    payer_shares = savings_green.deposit(claimable, bob, sender=bob)
    assert payer_shares == 10 * EIGHTEEN_DECIMALS
    savings_green.approve(teller, payer_shares, sender=bob)
    pool_shares_before = savings_green.balanceOf(stability_pool)
    supply_before = savings_green.totalSupply()
    vault_id = vault_book.getRegId(stability_pool)

    # The refund cutoff is strict: exactly 1e9 raw GREEN stays GREEN; one
    # additional unit is wrapped at the live (two-GREEN-per-share) rate.
    refund_cutoff = 10**9
    with boa.env.anchor():
        exact_payment = claimable + refund_cutoff
        bob_sgreen_before = savings_green.balanceOf(bob)
        green_token.transfer(bob, exact_payment, sender=whale)
        green_token.approve(teller, exact_payment, sender=bob)
        assert redeem_from_stability_pool(
            teller,
            vault_id,
            bravo_token,
            exact_payment,
            bob,
            False,
            False,
            True,
            sender=bob,
        ) == claimable
        assert green_token.balanceOf(bob) == refund_cutoff
        assert savings_green.balanceOf(bob) == bob_sgreen_before
        assert green_token.balanceOf(stability_pool) == 0
        assert green_token.allowance(stability_pool, savings_green) == 0

    with boa.env.anchor():
        wrapped_refund = refund_cutoff + 1
        above_cutoff_payment = claimable + wrapped_refund
        bob_sgreen_before = savings_green.balanceOf(bob)
        green_token.transfer(bob, above_cutoff_payment, sender=whale)
        green_token.approve(teller, above_cutoff_payment, sender=bob)
        assert redeem_from_stability_pool(
            teller,
            vault_id,
            bravo_token,
            above_cutoff_payment,
            bob,
            False,
            False,
            True,
            sender=bob,
        ) == claimable
        assert green_token.balanceOf(bob) == 0
        assert savings_green.balanceOf(bob) - bob_sgreen_before == (
            savings_green.convertToShares(wrapped_refund)
        )
        assert green_token.balanceOf(stability_pool) == 0
        assert green_token.allowance(stability_pool, savings_green) == 0

    green_spent = redeem_from_stability_pool(
        teller,
        vault_id,
        bravo_token,
        payer_shares,
        bob,
        False,
        True,
        True,
        sender=bob,
    )
    clear_transient_storage()

    assert green_spent == claimable
    assert bravo_token.balanceOf(bob) == claimable
    assert savings_green.balanceOf(bob) == 0
    assert savings_green.balanceOf(stability_pool) - pool_shares_before == payer_shares
    assert savings_green.totalSupply() == supply_before
    assert green_token.balanceOf(stability_pool) == 0
    assert green_token.allowance(stability_pool, savings_green) == 0
