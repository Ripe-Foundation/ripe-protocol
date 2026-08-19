import json
from pathlib import Path

import boa
import pytest
from eth_abi import encode
from eth_utils import keccak

from conf_utils import (
    claim_from_stability_pool,
    clear_transient_storage,
    filter_logs,
    redeem_from_stability_pool,
)
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ACTIVATION_THRESHOLD = 10 * 10**16
RETENTION_THRESHOLD = 5 * 10**16
CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2
DORMANT_BELOW_FLOOR = 1
DEACTIVATION_DUST = 2
DEACTIVATION_ZERO = 1
DECIMAL_OFFSET = 10**8
MAX_ACTIVE_CLAIM_ASSETS = 20
MAX_CLAIM_ASSET_MAINTENANCE = 15
ROOT = Path(__file__).resolve().parents[3]


def test_deployed_runtime_fits_eip170(stability_pool):
    """Assert the ceiling, not an exact size.

    This previously pinned `== 24_002`, which made any legitimate StabilityPool
    change a default-lane failure requiring a hand-refreshed constant. The
    property that protects a deployment is that the runtime fits.
    """
    runtime = boa.env.get_code(stability_pool.address)
    EIP170_LIMIT = 24_576
    print(
        "STABILITY_POOL_RUNTIME",
        f"size={len(runtime)}",
        f"headroom={EIP170_LIMIT - len(runtime)}",
    )
    assert len(runtime) <= EIP170_LIMIT


def test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        100 * EIGHTEEN_DECIMALS + MAX_ACTIVE_CLAIM_ASSETS,
    )
    claim_tokens = [
        _deploy_claim_token(
            governance,
            alice,
            1_300 + index,
            ACTIVATION_THRESHOLD + EIGHTEEN_DECIMALS,
        )
        for index in range(MAX_ACTIVE_CLAIM_ASSETS)
    ]

    target_counts = [
        0,
        1,
        2,
        4,
        8,
        12,
        MAX_CLAIM_ASSET_MAINTENANCE,
        MAX_ACTIVE_CLAIM_ASSETS,
    ]
    deposit_gas = []
    withdrawal_gas = []
    active_count = 0
    for target_count in target_counts:
        while active_count < target_count:
            token = claim_tokens[active_count]
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
            _record_claim(
                stability_pool,
                alpha_token,
                token,
                alice,
                ACTIVATION_THRESHOLD,
                bob,
                auction_house,
                green_token,
                savings_green,
            )
            active_count += 1

        assert stability_pool.getNumActiveClaimAssets(alpha_token) == target_count
        with boa.env.anchor():
            alpha_token.transfer(
                stability_pool,
                EIGHTEEN_DECIMALS,
                sender=alpha_token_whale,
            )
            gas_before = boa.env.get_gas_used()
            assert stability_pool.depositTokensInVault(
                alice,
                alpha_token,
                EIGHTEEN_DECIMALS,
                sender=teller.address,
            ) == EIGHTEEN_DECIMALS
            deposit_gas.append(boa.env.get_gas_used() - gas_before)

            gas_before = boa.env.get_gas_used()
            withdrawn, _ = stability_pool.withdrawTokensFromVault(
                alice,
                alpha_token,
                EIGHTEEN_DECIMALS,
                alice,
                sender=teller.address,
            )
            assert EIGHTEEN_DECIMALS - 1 <= withdrawn <= EIGHTEEN_DECIMALS
            withdrawal_gas.append(boa.env.get_gas_used() - gas_before)

    # Local-EVM regression ceilings for the actual value-moving calls. The
    # monotonic matrix proves the cap bounds the linear NAV traversal.
    assert all(a < b for a, b in zip(deposit_gas, deposit_gas[1:]))
    assert all(a < b for a, b in zip(withdrawal_gas, withdrawal_gas[1:]))
    # At the exact focused parent, the ceiling cases were 508,587 deposit and
    # 446,932 withdrawal. PriceDesk's guarded raw-call boundary adds 4,893 gas
    # to each (513,480 and 451,825). These deliberate ceilings retain 3.2% and
    # 4.0% local-EVM headroom without weakening the traversal checks.
    assert deposit_gas[-1] < 530_000
    assert withdrawal_gas[-1] < 470_000

    gas_before = boa.env.get_gas_used()
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, claim_tokens[0])
    liquidation_preflight_gas = boa.env.get_gas_used() - gas_before

    gas_before = boa.env.get_gas_used()
    asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)
    liquidation_iterator_gas = boa.env.get_gas_used() - gas_before
    assert asset == alpha_token.address
    assert amount == stability_pool.getTotalAmountForUser(bob, alpha_token)

    with boa.env.anchor():
        claim_tokens[0].transfer(stability_pool, 1, sender=alice)
        gas_before = boa.env.get_gas_used()
        assert stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            1,
            claim_tokens[0],
            1,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        ) == 1
        existing_receipt_gas = boa.env.get_gas_used() - gas_before

    setGeneralConfig()
    for token in claim_tokens:
        setAssetConfig(token)

    with boa.env.anchor():
        gas_before = boa.env.get_gas_used()
        assert stability_pool.claimManyFromStabilityPool(
            bob,
            [(alpha_token.address, claim_tokens[0].address, 10**15)],
            bob,
            False,
            sender=teller.address,
        ) != 0
        single_claim_gas = boa.env.get_gas_used() - gas_before

    with boa.env.anchor():
        claims = [
            (alpha_token.address, token.address, 10**15)
            for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]
        ]
        gas_before = boa.env.get_gas_used()
        assert stability_pool.claimManyFromStabilityPool(
            bob,
            claims,
            bob,
            False,
            sender=teller.address,
        ) != 0
        claim_many_gas = boa.env.get_gas_used() - gas_before

    # Last-share exit cannot finish while priced claimables remain in NAV.
    for start in range(0, MAX_ACTIVE_CLAIM_ASSETS, MAX_CLAIM_ASSET_MAINTENANCE):
        drain = [
            (alpha_token.address, token.address, MAX_UINT256)
            for token in claim_tokens[start:start + MAX_CLAIM_ASSET_MAINTENANCE]
        ]
        assert stability_pool.claimManyFromStabilityPool(
            bob,
            drain,
            bob,
            False,
            sender=teller.address,
        ) != 0
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0

    stability_pool.withdrawTokensFromVault(
        bob,
        alpha_token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert stability_pool.totalBalances(alpha_token) == 0

    alpha_token.transfer(
        stability_pool,
        MAX_ACTIVE_CLAIM_ASSETS * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    for token in claim_tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )

    for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]:
        mock_price_source.setPrice(token, 10**15)
    gas_before = boa.env.get_gas_used()
    stability_pool.pruneClaimableAssets(
        alpha_token,
        claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE],
        sender=alice,
    )
    prune_gas = boa.env.get_gas_used() - gas_before
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS - MAX_CLAIM_ASSET_MAINTENANCE
    )

    for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    gas_before = boa.env.get_gas_used()
    stability_pool.activateClaimAssets(
        alpha_token,
        claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE],
        sender=alice,
    )
    activation_gas = boa.env.get_gas_used() - gas_before
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )

    print(
        "STABILITY_ACTIVE_CLAIM_CEILING_GAS",
        f"deposit={deposit_gas[-1]}",
        f"withdrawal={withdrawal_gas[-1]}",
        f"claim_many={claim_many_gas}",
        f"prune={prune_gas}",
        f"activation={activation_gas}",
        f"active_claim_assets={MAX_ACTIVE_CLAIM_ASSETS}",
        f"maintenance_batch={MAX_CLAIM_ASSET_MAINTENANCE}",
    )

    # Local-EVM regression ceilings for the other public bounded paths. They
    # are not production gas estimates or assertions about a chain gas limit.
    assert existing_receipt_gas < 50_000
    assert prune_gas < 500_000
    assert activation_gas < 1_200_000
    assert single_claim_gas < 500_000
    # PR142 separately rebaselined its measured 7,013,069 parent value from the
    # obsolete 7,000,000 cap to 7,200,000. PriceDesk head is 7,089,959; this
    # final ceiling keeps ~2.3% local-EVM headroom and must not be conflated
    # with the 4,893-gas single deposit/withdrawal call delta.
    assert claim_many_gas < 7_250_000
    # Preflight and iteration each traverse the bounded claim set once. The
    # iterator must not repeat the strict NAV traversal after readiness passes.
    assert liquidation_preflight_gas < 600_000
    assert liquidation_iterator_gas < 600_000
    assert liquidation_iterator_gas < liquidation_preflight_gas + 100_000


def _exact_activation_price(pair_amount):
    return (ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + pair_amount - 1) // pair_amount


def _price_at_least_usd(pair_amount, usd):
    return (usd * EIGHTEEN_DECIMALS + pair_amount - 1) // pair_amount


def _price_at_most_usd(pair_amount, usd):
    return usd * EIGHTEEN_DECIMALS // pair_amount


def _exit_stab_cohort(stability_pool, stab, user, teller):
    stability_pool.withdrawTokensFromVault(
        user, stab, MAX_UINT256, user, sender=teller.address,
    )
    assert stability_pool.totalBalances(stab) == 0


def _seed_stability_asset(
    stability_pool,
    asset,
    whale,
    user,
    teller,
    mock_price_source,
    amount=100 * EIGHTEEN_DECIMALS,
):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(
        user,
        asset,
        amount,
        sender=teller.address,
    ) == amount


def _record_claim(
    stability_pool,
    stab_asset,
    claim_asset,
    claim_whale,
    claim_amount,
    recipient,
    auction_house,
    green_token,
    savings_green,
    stab_amount=1,
):
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset,
        stab_amount,
        claim_asset,
        claim_amount,
        recipient,
        green_token,
        savings_green,
        sender=auction_house.address,
    )


def _deposit_and_get_shares(
    stability_pool,
    asset,
    whale,
    user,
    teller,
    mock_price_source,
    amount,
):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    stability_pool.depositTokensInVault(
        user,
        asset,
        amount,
        sender=teller.address,
    )
    event = filter_logs(stability_pool, "StabilityPoolDeposit")[0]
    assert event.amount == amount
    assert event.shares == stability_pool.userBalances(user, asset)
    return event.shares


def test_withdrawal_rounds_shares_up_at_exact_remainder_boundary(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    deposited = 5
    shares = _deposit_and_get_shares(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        deposited,
    )
    balance_before = alpha_token.balanceOf(bob)
    withdrawn, depleted = stability_pool.withdrawTokensFromVault(
        bob,
        alpha_token,
        1,
        bob,
        sender=teller.address,
    )
    expected_burn = (shares + DECIMAL_OFFSET) // (deposited + 1)
    event = filter_logs(stability_pool, "StabilityPoolWithdrawal")[0]
    assert withdrawn == 1
    assert not depleted
    assert event.shares == expected_burn == DECIMAL_OFFSET
    assert stability_pool.userBalances(bob, alpha_token) == shares - expected_burn
    assert stability_pool.totalBalances(alpha_token) == shares - expected_burn
    assert alpha_token.balanceOf(bob) == balance_before + 1
    assert alpha_token.balanceOf(stability_pool) == deposited - 1


def test_withdrawal_rounding_boundary_below_exact_above(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    deposited = 5
    shares = _deposit_and_get_shares(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        deposited,
    )
    donation = 3
    alpha_token.transfer(stability_pool, donation, sender=alpha_token_whale)
    denominator = deposited + donation + 1
    multiplier = shares + DECIMAL_OFFSET

    for amount in (2, 3, 4):
        with boa.env.anchor():
            user_before = alpha_token.balanceOf(bob)
            withdrawn, _ = stability_pool.withdrawTokensFromVault(
                bob,
                alpha_token,
                amount,
                bob,
                sender=teller.address,
            )
            numerator = amount * multiplier
            expected_burn = numerator // denominator
            if numerator % denominator:
                expected_burn += 1
            event = filter_logs(stability_pool, "StabilityPoolWithdrawal")[0]
            assert withdrawn == amount
            assert event.shares == expected_burn
            assert stability_pool.userBalances(bob, alpha_token) == shares - expected_burn
            assert stability_pool.totalBalances(alpha_token) == shares - expected_burn
            assert alpha_token.balanceOf(bob) == user_before + amount
            assert alpha_token.balanceOf(stability_pool) == deposited + donation - amount
    assert (2 * multiplier) % denominator != 0
    assert (3 * multiplier) % denominator == 0
    assert (4 * multiplier) % denominator != 0


def test_direct_donation_cannot_create_zero_share_or_value_capture_deposit(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
):
    alice_shares = _deposit_and_get_shares(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        alice,
        teller,
        mock_price_source,
        1,
    )
    donation = DECIMAL_OFFSET - 1
    alpha_token.transfer(stability_pool, donation, sender=alpha_token_whale)
    alpha_token.transfer(stability_pool, 1, sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        1,
        sender=teller.address,
    ) == 1
    bob_shares = stability_pool.userBalances(bob, alpha_token)
    assert bob_shares == 1
    assert stability_pool.totalBalances(alpha_token) == alice_shares + bob_shares
    assert stability_pool.getTotalAmountForUser(bob, alpha_token) <= 1
    assert stability_pool.getTotalAmountForUser(alice, alpha_token) == donation + 1
    assert alpha_token.balanceOf(stability_pool) == donation + 2


def test_decimal_offset_one_unit_boundary_preserves_accounting(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    shares = _deposit_and_get_shares(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        1,
    )
    assert shares == DECIMAL_OFFSET
    withdrawn, depleted = stability_pool.withdrawTokensFromVault(
        bob,
        alpha_token,
        1,
        bob,
        sender=teller.address,
    )
    event = filter_logs(stability_pool, "StabilityPoolWithdrawal")[0]
    assert withdrawn == 1
    assert depleted
    assert event.shares == shares
    assert stability_pool.userBalances(bob, alpha_token) == 0
    assert stability_pool.totalBalances(alpha_token) == 0
    assert alpha_token.balanceOf(stability_pool) == 0


def _deploy_claim_token(governance, holder, index, amount=EIGHTEEN_DECIMALS):
    token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        f"Hard Claim {index}",
        f"HC{index}",
        18,
        0,
        name=f"hard_claim_{index}",
    )
    token.mint(holder, amount, sender=governance.address)
    return token


def _asset_address(asset):
    return asset.address if hasattr(asset, "address") else asset


def _claim_pair(stab_asset, claim_asset):
    return _asset_address(stab_asset), _asset_address(claim_asset)


def _assert_claim_data_model(
    stability_pool,
    stab_assets,
    claim_assets,
    expected_pair_balances,
    expected_active_assets,
    expected_num_claimable_assets,
    expected_custody_shortfalls=None,
):
    """Assert the complete externally observable claim-accounting model."""
    custody_shortfalls = expected_custody_shortfalls or {}

    for stab_asset in stab_assets:
        stab_address = _asset_address(stab_asset)
        active_assets = expected_active_assets[stab_address]
        active_addresses = [_asset_address(asset) for asset in active_assets]

        assert len(active_addresses) == len(set(active_addresses))
        assert stability_pool.numClaimableAssets(stab_asset) == (
            expected_num_claimable_assets[stab_address]
        )
        assert stability_pool.getNumActiveClaimAssets(stab_asset) == len(
            active_assets
        )
        assert stability_pool.claimableAssets(stab_asset, 0) == ZERO_ADDRESS

        # Check every possible occupied slot plus one tail slot. This catches
        # holes, duplicates, and stale values left behind by swap-and-pop.
        for index in range(1, len(claim_assets) + 2):
            expected_asset = (
                active_addresses[index - 1]
                if index <= len(active_addresses)
                else ZERO_ADDRESS
            )
            assert stability_pool.claimableAssets(stab_asset, index) == (
                expected_asset
            )

        for claim_asset in claim_assets:
            claim_address = _asset_address(claim_asset)
            expected_balance = expected_pair_balances.get(
                (stab_address, claim_address),
                0,
            )
            expected_index = (
                active_addresses.index(claim_address) + 1
                if claim_address in active_addresses
                else 0
            )

            assert stability_pool.claimableBalances(
                stab_asset,
                claim_asset,
            ) == expected_balance
            assert stability_pool.indexOfClaimableAsset(
                stab_asset,
                claim_asset,
            ) == expected_index

            if expected_index != 0:
                assert expected_balance != 0
                expected_state = CLAIM_ASSET_ACTIVE
            elif expected_balance != 0:
                expected_state = CLAIM_ASSET_DORMANT
            else:
                expected_state = CLAIM_ASSET_ABSENT
            assert stability_pool.getClaimAssetState(
                stab_asset,
                claim_asset,
            ) == expected_state

    # Aggregate liability must equal the sum of every pair in the model. Token
    # custody must cover it except where a test deliberately models a deficit.
    for claim_asset in claim_assets:
        claim_address = _asset_address(claim_asset)
        expected_total = sum(
            expected_pair_balances.get(
                (_asset_address(stab_asset), claim_address),
                0,
            )
            for stab_asset in stab_assets
        )
        assert stability_pool.totalClaimableBalances(claim_asset) == (
            expected_total
        )

        custody = claim_asset.balanceOf(stability_pool)
        expected_shortfall = custody_shortfalls.get(claim_address, 0)
        if expected_shortfall == 0:
            assert custody >= expected_total
        else:
            assert expected_total - custody == expected_shortfall


def test_receipts_accumulate_then_activate_once_at_exact_floor(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    first_amount = ACTIVATION_THRESHOLD - 1
    assert _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        first_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1

    dormant = filter_logs(stability_pool, "ClaimAssetLeftDormant")
    assert len(dormant) == 1
    assert dormant[0].balance == first_amount
    assert dormant[0].activeCount == 0
    assert dormant[0].reason == DORMANT_BELOW_FLOOR
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == first_amount
    assert stability_pool.totalClaimableBalances(bravo_token) == first_amount
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0

    # Known sub-floor dust is deliberately non-blocking.
    with boa.env.anchor():
        alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        assert stability_pool.depositTokensInVault(
            bob,
            alpha_token,
            EIGHTEEN_DECIMALS,
            sender=teller.address,
        ) == EIGHTEEN_DECIMALS

    assert _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        1,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1

    activated = filter_logs(stability_pool, "ClaimAssetActivated")
    assert len(activated) == 1
    assert activated[0].balance == ACTIVATION_THRESHOLD
    assert activated[0].activeCount == 1
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(bravo_token) == ACTIVATION_THRESHOLD
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address

    mock_price_source.disablePriceFeed(bravo_token)
    assert _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        1,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    assert filter_logs(stability_pool, "ClaimAssetLeftDormant") == []
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == ACTIVATION_THRESHOLD + 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1


def test_unpriced_new_receipt_reverts_without_claim_accounting(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, 0)

    amount = EIGHTEEN_DECIMALS
    with boa.env.anchor():
        with boa.reverts("no price for claim asset"):
            _record_claim(
                stability_pool,
                alpha_token,
                bravo_token,
                bravo_token_whale,
                amount,
                bob,
                auction_house,
                green_token,
                savings_green,
            )
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
        assert stability_pool.totalClaimableBalances(bravo_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ABSENT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0

    assert bravo_token.balanceOf(stability_pool) == 0
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert not stability_pool.canAcceptLiquidationAsset(bravo_token, alpha_token)


def test_active_zero_price_stays_registered_and_recovers_after_price_restore(
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
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        ACTIVATION_THRESHOLD,
        bob,
        auction_house,
        green_token,
        savings_green,
    )

    total_value_before = stability_pool.getTotalValue(alpha_token)
    shares_before = stability_pool.userBalances(bob, alpha_token)
    custody_before = bravo_token.balanceOf(stability_pool)
    pair_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    liability_before = stability_pool.totalClaimableBalances(bravo_token)
    active_index = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert active_index != 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # An active claim liability cannot silently disappear from NAV. A zero
    # price therefore blocks valuation and share-changing operations while the
    # active registration and all accounting remain intact.
    mock_price_source.setPrice(bravo_token, 0)
    with boa.reverts():
        stability_pool.getTotalValue(alpha_token)
    with boa.reverts():
        stability_pool.getTotalUserValue(bob, alpha_token)

    with boa.env.anchor():
        alpha_token.transfer(
            stability_pool,
            EIGHTEEN_DECIMALS,
            sender=alpha_token_whale,
        )
        with boa.reverts():
            stability_pool.depositTokensInVault(
                alice,
                alpha_token,
                EIGHTEEN_DECIMALS,
                sender=teller.address,
            )
        with boa.reverts():
            stability_pool.withdrawTokensFromVault(
                bob,
                alpha_token,
                EIGHTEEN_DECIMALS,
                bob,
                sender=teller.address,
            )
        assert stability_pool.userBalances(bob, alpha_token) == shares_before

    # Maintenance never removes or reclassifies an unpriced active pair,
    # whether the pool is paused or unpaused.
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [bravo_token, bravo_token],
        sender=alice,
    )
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == active_index
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair_before
    assert stability_pool.totalClaimableBalances(bravo_token) == liability_before
    assert bravo_token.balanceOf(stability_pool) == custody_before
    assert stability_pool.userBalances(bob, alpha_token) == shares_before

    # Unpause has no oracle-specific state machine. Removing the feed entirely
    # retains the same fail-closed valuation behavior.
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert not stability_pool.isPaused()
    mock_price_source.disablePriceFeed(bravo_token)
    with boa.reverts():
        stability_pool.getTotalValue(alpha_token)

    # Restoring the feed puts the collateral back into NAV immediately; no
    # activation call or persistent recovery bookkeeping is required.
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert stability_pool.getTotalValue(alpha_token) == total_value_before
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

def test_prune_skips_unpriced_pair_and_continues_batch_while_paused_or_unpaused(
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
    green_token,
    savings_green,
    switchboard_alpha,
):
    bravo_amount = ACTIVATION_THRESHOLD - 1
    charlie_amount = 50_000  # 6dp; $0.05 at $1, dormant until empty-activate
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    for claim_asset, whale, amount in (
        (bravo_token, bravo_token_whale, bravo_amount),
        (charlie_token, charlie_token_whale, charlie_amount),
    ):
        mock_price_source.setPrice(claim_asset, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            claim_asset,
            whale,
            amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, claim_asset,
        ) == CLAIM_ASSET_DORMANT
    _exit_stab_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(
        stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale,
    )
    mock_price_source.setPrice(bravo_token, _exact_activation_price(bravo_amount))
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(
        alpha_token, [bravo_token, charlie_token], sender=alice,
    )
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_ACTIVE

    bravo_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    charlie_balance = stability_pool.claimableBalances(alpha_token, charlie_token)
    bravo_index = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    mock_price_source.setPrice(bravo_token, 0)
    mock_price_source.setPrice(charlie_token, 4 * 10**17)

    stability_pool.pruneClaimableAssets(
        alpha_token,
        [bravo_token, charlie_token],
        sender=alice,
    )

    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == charlie_token.address
    assert logs[0].reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == bravo_index
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == bravo_balance
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == charlie_balance

    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == bravo_index


def test_dormant_thresholds_have_exact_hysteresis_boundaries(
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
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pair_amount = ACTIVATION_THRESHOLD - 1
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        pair_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_DORMANT

    _exit_stab_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(
        stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale,
    )
    mock_price_source.setPrice(bravo_token, _exact_activation_price(pair_amount))
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE

    # Exact $0.05 remains active; immediately below it prunes. The band from
    # $0.05 through $0.099... therefore preserves the existing state.
    mock_price_source.setPrice(
        bravo_token, _price_at_least_usd(pair_amount, RETENTION_THRESHOLD),
    )
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(
        bravo_token, _price_at_most_usd(pair_amount, RETENTION_THRESHOLD - 1),
    )
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_DORMANT

    activation_price = _exact_activation_price(pair_amount)
    mock_price_source.setPrice(bravo_token, _price_at_most_usd(pair_amount, ACTIVATION_THRESHOLD - 1))
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_DORMANT
    mock_price_source.setPrice(bravo_token, activation_price)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE


def test_zero_raw_balance_with_only_dormant_claim_is_explicit_exit_residual(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    dormant_amount = ACTIVATION_THRESHOLD - 1
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        dormant_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
        EIGHTEEN_DECIMALS,
    )

    assert alpha_token.balanceOf(stability_pool) == 0
    assert stability_pool.getTotalValue(alpha_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    shares_before = stability_pool.userBalances(bob, alpha_token)
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller,
            vault_book.getRegId(stability_pool),
            alpha_token,
            bravo_token,
            sender=bob,
        )
    assert stability_pool.userBalances(bob, alpha_token) == shares_before
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == dormant_amount
    assert stability_pool.totalClaimableBalances(bravo_token) == dormant_amount


def test_activation_floor_is_decimal_independent(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    delta_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )

    cases = (
        (bravo_token, bravo_token_whale, 10 * 10**16),
        (charlie_token, charlie_token_whale, 100_000),
        (delta_token, delta_token_whale, 10_000_000),
    )
    for expected_index, (token, whale, amount) in enumerate(cases, start=1):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        assert _record_claim(
            stability_pool,
            alpha_token,
            token,
            whale,
            amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        ) == 1
        assert stability_pool.getClaimAssetState(alpha_token, token) == CLAIM_ASSET_ACTIVE
        assert stability_pool.indexOfClaimableAsset(alpha_token, token) == expected_index

    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 3


def test_cap_rejects_new_receipt_then_prune_allows_activation(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )

    tokens = []
    for index in range(MAX_ACTIVE_CLAIM_ASSETS + 1):
        token = _deploy_claim_token(governance, alice, index, ACTIVATION_THRESHOLD)
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        tokens.append(token)

    for token in tokens[:MAX_ACTIVE_CLAIM_ASSETS]:
        assert _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        ) == 1

    candidate = tokens[MAX_ACTIVE_CLAIM_ASSETS]
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )
    assert stability_pool.numClaimableAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS + 1
    )
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, tokens[0])
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)
    assert stability_pool.getClaimAssetState(alpha_token, candidate) == CLAIM_ASSET_ABSENT

    # The pool-level assertion is defense in depth for a caller that ignores
    # the preflight. No claim accounting changes when the call fails.
    with boa.env.anchor():
        with boa.reverts("max active claim assets"):
            _record_claim(
                stability_pool,
                alpha_token,
                candidate,
                alice,
                ACTIVATION_THRESHOLD,
                bob,
                auction_house,
                green_token,
                savings_green,
            )
        assert stability_pool.claimableBalances(alpha_token, candidate) == 0
        assert stability_pool.totalClaimableBalances(candidate) == 0

    # Reaching the cap does not freeze deposits because no material value was
    # accepted outside the active NAV list.
    with boa.env.anchor():
        alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        assert stability_pool.depositTokensInVault(
            alice,
            alpha_token,
            EIGHTEEN_DECIMALS,
            sender=teller.address,
        ) == EIGHTEEN_DECIMALS

    stab_address = _asset_address(alpha_token)
    expected_pairs = {
        _claim_pair(alpha_token, token): ACTIVATION_THRESHOLD
        for token in tokens[:MAX_ACTIVE_CLAIM_ASSETS]
    }
    expected_active = {stab_address: tokens[:MAX_ACTIVE_CLAIM_ASSETS]}
    expected_num_assets = {stab_address: MAX_ACTIVE_CLAIM_ASSETS + 1}
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    removed = tokens[4]
    moved = tokens[MAX_ACTIVE_CLAIM_ASSETS - 1]
    assert stability_pool.indexOfClaimableAsset(alpha_token, removed) == 5
    assert stability_pool.indexOfClaimableAsset(alpha_token, moved) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )
    setAssetConfig(removed)
    stability_pool.claimManyFromStabilityPool(
        bob,
        [(alpha_token.address, removed.address, MAX_UINT256)],
        bob,
        False,
        sender=teller.address,
    )
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS - 1
    )
    assert stability_pool.getClaimAssetState(alpha_token, removed) == CLAIM_ASSET_ABSENT
    assert stability_pool.claimableBalances(alpha_token, removed) == 0
    assert stability_pool.claimableAssets(alpha_token, 5) == moved.address
    assert stability_pool.indexOfClaimableAsset(alpha_token, moved) == 5

    expected_pairs[_claim_pair(alpha_token, removed)] = 0
    expected_active[stab_address] = (
        tokens[:4]
        + [tokens[MAX_ACTIVE_CLAIM_ASSETS - 1]]
        + tokens[5 : MAX_ACTIVE_CLAIM_ASSETS - 1]
    )
    expected_num_assets[stab_address] = MAX_ACTIVE_CLAIM_ASSETS
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    assert stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)
    assert _record_claim(
        stability_pool,
        alpha_token,
        candidate,
        alice,
        ACTIVATION_THRESHOLD,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )
    assert stability_pool.numClaimableAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS + 1
    )
    assert stability_pool.getClaimAssetState(alpha_token, candidate) == CLAIM_ASSET_ACTIVE
    assert stability_pool.indexOfClaimableAsset(alpha_token, candidate) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )
    assert stability_pool.claimableAssets(
        alpha_token,
        MAX_ACTIVE_CLAIM_ASSETS,
    ) == candidate.address
    assert stability_pool.claimableBalances(alpha_token, candidate) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(candidate) == ACTIVATION_THRESHOLD
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, removed)

    expected_pairs[_claim_pair(alpha_token, candidate)] = ACTIVATION_THRESHOLD
    expected_active[stab_address].append(candidate)
    expected_num_assets[stab_address] = MAX_ACTIVE_CLAIM_ASSETS + 1
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    seen = set()
    for index in range(1, MAX_ACTIVE_CLAIM_ASSETS + 1):
        asset = stability_pool.claimableAssets(alpha_token, index)
        assert asset != ZERO_ADDRESS
        assert asset not in seen
        assert stability_pool.indexOfClaimableAsset(alpha_token, asset) == index
        seen.add(asset)


def test_receipt_checks_global_liability_across_stability_assets(
    stability_pool,
    alpha_token,
    charlie_token,
    alpha_token_whale,
    charlie_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    _seed_stability_asset(
        stability_pool,
        charlie_token,
        charlie_token_whale,
        bob,
        teller,
        mock_price_source,
        100 * 10**6,
    )
    claim = _deploy_claim_token(
        governance,
        alice,
        50,
        2 * ACTIVATION_THRESHOLD,
    )
    mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)

    assert _record_claim(
        stability_pool,
        alpha_token,
        claim,
        alice,
        ACTIVATION_THRESHOLD,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1
    assert _record_claim(
        stability_pool,
        charlie_token,
        claim,
        alice,
        ACTIVATION_THRESHOLD,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1

    total = 2 * ACTIVATION_THRESHOLD
    assert stability_pool.claimableBalances(alpha_token, claim) == ACTIVATION_THRESHOLD
    assert stability_pool.claimableBalances(charlie_token, claim) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(claim) == total
    assert claim.balanceOf(stability_pool) == total

    claim.transfer(alice, 1, sender=stability_pool.address)
    assert claim.balanceOf(stability_pool) == total - 1
    with boa.reverts("claim custody deficit"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            1,
            claim,
            1,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        )

    assert stability_pool.claimableBalances(alpha_token, claim) == ACTIVATION_THRESHOLD
    assert stability_pool.claimableBalances(charlie_token, claim) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(claim) == total


def test_short_receipt_and_later_swap_failure_roll_back_accounting(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    claim = _deploy_claim_token(governance, alice, 60, 2 * ACTIVATION_THRESHOLD)
    mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)

    claim.transfer(stability_pool, ACTIVATION_THRESHOLD - 1, sender=alice)
    with boa.reverts("short claim receipt"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            1,
            claim,
            ACTIVATION_THRESHOLD,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        )
    assert stability_pool.claimableBalances(alpha_token, claim) == 0
    assert stability_pool.totalClaimableBalances(claim) == 0
    assert stability_pool.getClaimAssetState(alpha_token, claim) == CLAIM_ASSET_ABSENT

    claim.transfer(stability_pool, 1, sender=alice)
    with boa.reverts("must be green or savings green"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            1,
            claim,
            ACTIVATION_THRESHOLD,
            ZERO_ADDRESS,
            green_token,
            savings_green,
            sender=auction_house.address,
        )
    assert claim.balanceOf(stability_pool) == ACTIVATION_THRESHOLD
    assert stability_pool.claimableBalances(alpha_token, claim) == 0
    assert stability_pool.totalClaimableBalances(claim) == 0
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0


def test_stability_pool_recovery_entrypoints_are_disabled_for_all_callers(
    stability_pool,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    switchboard_alpha,
):
    alpha_token.transfer(stability_pool, 50, sender=alpha_token_whale)
    pool_shares_before = stability_pool.totalBalances(alpha_token)
    for caller in (switchboard_alpha.address, bob, alice):
        with boa.reverts():
            stability_pool.recoverFunds(
                bob,
                alpha_token,
                sender=caller,
            )
        with boa.reverts():
            stability_pool.recoverFundsMany(
                bob,
                [alpha_token],
                sender=caller,
            )
        assert alpha_token.balanceOf(stability_pool) == 50
        assert alpha_token.balanceOf(bob) == 0
        assert stability_pool.totalBalances(alpha_token) == pool_shares_before

    alpha_token.transfer(simple_erc20_vault, 50, sender=alpha_token_whale)
    simple_erc20_vault.recoverFunds(
        bob,
        alpha_token,
        sender=switchboard_alpha.address,
    )
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert alpha_token.balanceOf(bob) == 50


def test_removed_conversion_selectors_are_not_callable_at_runtime(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    probe = boa.loads(
        """# @version 0.4.3

@external
def call_succeeds(_target: address, _data: Bytes[256]) -> bool:
    success: bool = False
    response: Bytes[4096] = b""
    success, response = raw_call(
        _target,
        _data,
        max_outsize=4096,
        revert_on_failure=False,
        is_static_call=True,
    )
    return success
""",
        name="removed_stability_selector_probe",
    )
    args = encode(("address", "uint256", "bool"), (alpha_token.address, 1, False))
    for signature in (
        "valueToShares(address,uint256,bool)",
        "sharesToValue(address,uint256,bool)",
    ):
        assert not probe.call_succeeds(
            stability_pool,
            keccak(text=signature)[:4] + args,
        )
    control = keccak(text="getTotalAmountForVault(address)")[:4] + encode(
        ("address",),
        (alpha_token.address,),
    )
    assert probe.call_succeeds(stability_pool, control)


def test_green_cannot_be_stability_asset_but_remains_valid_claim_asset(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    with boa.reverts("green cannot be stab asset"):
        stability_pool.depositTokensInVault(
            bob,
            green_token,
            1,
            sender=teller.address,
        )

    for swap in (
        lambda: stability_pool.swapForLiquidatedCollateral(
            green_token,
            1,
            bravo_token,
            1,
            bob,
            green_token,
            savings_green,
            sender=auction_house.address,
        ),
        lambda: stability_pool.swapWithClaimableGreen(
            green_token,
            1,
            bravo_token,
            1,
            green_token,
            sender=auction_house.address,
        ),
    ):
        with boa.reverts("stab asset not supported"):
            swap()

    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    green_token.transfer(stability_pool, ACTIVATION_THRESHOLD, sender=whale)
    assert stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        green_token,
        ACTIVATION_THRESHOLD,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    ) == 1

    assert stability_pool.claimableBalances(alpha_token, green_token) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(green_token) == ACTIVATION_THRESHOLD
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
    assert stability_pool.claimableBalances(green_token, green_token) == 0


def test_green_asset_identity_does_not_change_after_hq_repoint(
    stability_pool,
    ripe_hq_deploy,
    governance,
    alice,
    bob,
    whale,
    teller,
    auction_house,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    green_token.transfer(stability_pool, ACTIVATION_THRESHOLD, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        green_token,
        ACTIVATION_THRESHOLD,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    total_before = stability_pool.getTotalValue(alpha_token)
    replacement_green = _deploy_claim_token(
        governance,
        alice,
        100,
        EIGHTEEN_DECIMALS,
    )

    with boa.env.anchor():
        assert ripe_hq_deploy.startAddressUpdateToRegistry(
            1,
            replacement_green,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
        assert ripe_hq_deploy.confirmAddressUpdateToRegistry(
            1,
            sender=governance.address,
        )
        assert stability_pool.getAddys().greenToken == replacement_green.address
        assert stability_pool.getTotalValue(alpha_token) == total_before

        replacement_green.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alice)
        with boa.reverts("green cannot be stab asset"):
            stability_pool.depositTokensInVault(
                alice,
                replacement_green,
                EIGHTEEN_DECIMALS,
                sender=teller.address,
            )


def test_savings_green_asset_identity_does_not_change_after_hq_repoint(
    stability_pool,
    ripe_hq_deploy,
    governance,
    alice,
    bob,
    whale,
    teller,
    auction_house,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    green_token.transfer(alice, ACTIVATION_THRESHOLD, sender=whale)
    green_token.approve(savings_green, ACTIVATION_THRESHOLD, sender=alice)
    savings_green.deposit(ACTIVATION_THRESHOLD, alice, sender=alice)
    savings_amount = savings_green.balanceOf(alice)
    assert savings_amount > 0
    savings_green.transfer(stability_pool, savings_amount, sender=alice)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        savings_green,
        savings_amount,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    total_before = stability_pool.getTotalValue(alpha_token)
    replacement = _deploy_claim_token(
        governance,
        alice,
        101,
        EIGHTEEN_DECIMALS,
    )

    with boa.env.anchor():
        assert ripe_hq_deploy.startAddressUpdateToRegistry(
            2,
            replacement,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
        assert ripe_hq_deploy.confirmAddressUpdateToRegistry(
            2,
            sender=governance.address,
        )
        assert stability_pool.getAddys().savingsGreen == replacement.address
        assert stability_pool.getTotalValue(alpha_token) == total_before


def test_claimable_green_swap_depletes_active_pair_and_emits_deactivation_zero_reason_one(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    pair_amount = ACTIVATION_THRESHOLD
    green_token.transfer(stability_pool, pair_amount, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        green_token,
        pair_amount,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.indexOfClaimableAsset(alpha_token, green_token) == 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1

    fresh_receipt = 1
    green_token.transfer(stability_pool, fresh_receipt, sender=whale)
    burned = stability_pool.swapWithClaimableGreen(
        alpha_token,
        pair_amount + fresh_receipt,
        green_token,
        fresh_receipt,
        green_token,
        sender=auction_house.address,
    )
    assert burned == pair_amount + fresh_receipt
    events = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(events) == 1
    event = events[0]
    assert event.stabAsset == alpha_token.address
    assert event.claimAsset == green_token.address
    assert event.balance == 0
    assert event.activeCount == 0
    assert event.reason == DEACTIVATION_ZERO
    assert stability_pool.indexOfClaimableAsset(alpha_token, green_token) == 0
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.claimableBalances(alpha_token, green_token) == 0
    assert stability_pool.totalClaimableBalances(green_token) == 0


def test_full_pool_accepts_existing_claims_and_keeps_deposits_open(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        100 * EIGHTEEN_DECIMALS + 14,
    )

    active_assets = []
    for index in range(MAX_ACTIVE_CLAIM_ASSETS):
        asset = _deploy_claim_token(governance, alice, index + 200, ACTIVATION_THRESHOLD + 1)
        mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            asset,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        active_assets.append(asset)

    candidate = _deploy_claim_token(
        governance,
        alice,
        300,
        ACTIVATION_THRESHOLD,
    )
    mock_price_source.setPrice(candidate, EIGHTEEN_DECIMALS)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
        assert stability_pool.depositTokensInVault(
            alice,
            alpha_token,
            deposit_amount,
            sender=teller.address,
        ) == deposit_amount

    # A receipt for an already-active pair still requires no additional slot.
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, active_assets[0])
    assert _record_claim(
        stability_pool,
        alpha_token,
        active_assets[0],
        alice,
        1,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1
    assert stability_pool.claimableBalances(alpha_token, active_assets[0]) == ACTIVATION_THRESHOLD + 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS
    )
    assert stability_pool.getClaimAssetState(alpha_token, candidate) == CLAIM_ASSET_ABSENT


def test_claim_data_model_survives_batched_lifecycle_mutations(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    switchboard_alpha,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )

    tokens = [
        _deploy_claim_token(
            governance,
            alice,
            400 + index,
            ACTIVATION_THRESHOLD,
        )
        for index in range(5)
    ]
    initial_prices = [
        EIGHTEEN_DECIMALS,
        EIGHTEEN_DECIMALS,
        EIGHTEEN_DECIMALS,
        EIGHTEEN_DECIMALS // 2,
        2 * 10**17,
    ]
    for token, price in zip(tokens, initial_prices):
        mock_price_source.setPrice(token, price)

    stab_address = _asset_address(alpha_token)
    expected_pairs = {}
    expected_active = {stab_address: []}
    expected_num_assets = {stab_address: 0}

    for index, token in enumerate(tokens):
        _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        expected_pairs[_claim_pair(alpha_token, token)] = ACTIVATION_THRESHOLD
        if index < 3:
            expected_active[stab_address].append(token)
            expected_num_assets[stab_address] = (
                len(expected_active[stab_address]) + 1
            )

        _assert_claim_data_model(
            stability_pool,
            [alpha_token],
            tokens,
            expected_pairs,
            expected_active,
            expected_num_assets,
        )

    # Live book: dust prune and activate are membership no-ops.
    mock_price_source.setPrice(tokens[1], 2 * 10**17)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [tokens[1], tokens[1], tokens[4], ZERO_ADDRESS],
        sender=alice,
    )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    mock_price_source.setPrice(tokens[3], EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(tokens[4], EIGHTEEN_DECIMALS)
    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(
            alpha_token,
            [tokens[3], tokens[4]],
            sender=alice,
        )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(
        alpha_token,
        [tokens[3], tokens[4], tokens[3], ZERO_ADDRESS],
        sender=alice,
    )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    stability_pool.activateClaimAssets(
        alpha_token,
        [tokens[4], tokens[0], tokens[4], ZERO_ADDRESS],
        sender=alice,
    )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    mock_price_source.setPrice(tokens[0], 2 * 10**17)
    mock_price_source.setPrice(tokens[3], 2 * 10**17)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [tokens[0], tokens[3]],
        sender=alice,
    )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )


def test_claim_data_batch_activation_reverts_atomically_on_custody_deficit(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    switchboard_alpha,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    healthy = _deploy_claim_token(
        governance,
        alice,
        500,
        ACTIVATION_THRESHOLD,
    )
    deficient = _deploy_claim_token(
        governance,
        alice,
        501,
        ACTIVATION_THRESHOLD,
    )
    tokens = [healthy, deficient]
    for token in tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS // 2)
        _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, MAX_UINT256, bob, sender=teller.address,
    )
    assert stability_pool.totalBalances(alpha_token) == 0

    stab_address = _asset_address(alpha_token)
    expected_pairs = {
        _claim_pair(alpha_token, healthy): ACTIVATION_THRESHOLD,
        _claim_pair(alpha_token, deficient): ACTIVATION_THRESHOLD,
    }
    expected_active = {stab_address: []}
    expected_num_assets = {stab_address: 0}
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    for token in tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    deficient.transfer(alice, 1, sender=stability_pool.address)
    stability_pool.pause(True, sender=switchboard_alpha.address)

    # The healthy entry is processed first. The later deficit must roll back
    # that registration and leave the whole batch unchanged.
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(
            alpha_token,
            [healthy, deficient],
            sender=alice,
        )
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
        {_asset_address(deficient): 1},
    )

    deficient.transfer(stability_pool, 1, sender=alice)
    stability_pool.activateClaimAssets(
        alpha_token,
        [healthy, deficient],
        sender=alice,
    )
    expected_active[stab_address] = [healthy, deficient]
    expected_num_assets[stab_address] = 3
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )


def test_claim_data_model_tracks_dust_claim_reactivation_and_zero_removal(
    stability_pool,
    alpha_token,
    charlie_token,
    alpha_token_whale,
    charlie_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    _seed_stability_asset(
        stability_pool,
        charlie_token,
        charlie_token_whale,
        bob,
        teller,
        mock_price_source,
        100 * 10**6,
    )

    partial_claim = 6 * 10**16
    claim = _deploy_claim_token(
        governance,
        alice,
        600,
        2 * ACTIVATION_THRESHOLD + partial_claim,
    )
    setAssetConfig(claim)
    mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)

    for stab_asset in (alpha_token, charlie_token):
        _record_claim(
            stability_pool,
            stab_asset,
            claim,
            alice,
            ACTIVATION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )

    stab_assets = [alpha_token, charlie_token]
    claim_assets = [claim]
    alpha_address = _asset_address(alpha_token)
    charlie_address = _asset_address(charlie_token)
    expected_pairs = {
        _claim_pair(alpha_token, claim): ACTIVATION_THRESHOLD,
        _claim_pair(charlie_token, claim): ACTIVATION_THRESHOLD,
    }
    expected_active = {
        alpha_address: [claim],
        charlie_address: [claim],
    }
    expected_num_assets = {
        alpha_address: 2,
        charlie_address: 2,
    }
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    balance_before = claim.balanceOf(bob)
    claimed_usd_value = stability_pool.claimManyFromStabilityPool(
        bob,
        [(alpha_token.address, claim.address, partial_claim)],
        bob,
        False,
        sender=teller.address,
    )
    claimed_amount = claim.balanceOf(bob) - balance_before
    assert claimed_usd_value != 0
    assert 0 < claimed_amount <= partial_claim

    remaining = ACTIVATION_THRESHOLD - claimed_amount
    assert 0 < remaining < RETENTION_THRESHOLD
    expected_pairs[_claim_pair(alpha_token, claim)] = remaining
    expected_active[alpha_address] = [claim]
    expected_num_assets[alpha_address] = 2
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # A later receipt restores the cumulative pair exactly to the activation
    # floor and reuses the sentinel registry without touching the other pair.
    top_up = ACTIVATION_THRESHOLD - remaining
    _record_claim(
        stability_pool,
        alpha_token,
        claim,
        alice,
        top_up,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    expected_pairs[_claim_pair(alpha_token, claim)] = ACTIVATION_THRESHOLD
    expected_active[alpha_address] = [claim]
    expected_num_assets[alpha_address] = 2
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    for stab_asset, stab_address in (
        (alpha_token, alpha_address),
        (charlie_token, charlie_address),
    ):
        balance_before = claim.balanceOf(bob)
        stability_pool.claimManyFromStabilityPool(
            bob,
            [(stab_asset.address, claim.address, MAX_UINT256)],
            bob,
            False,
            sender=teller.address,
        )
        assert claim.balanceOf(bob) - balance_before == ACTIVATION_THRESHOLD
        expected_pairs[_claim_pair(stab_asset, claim)] = 0
        expected_active[stab_address] = []
        expected_num_assets[stab_address] = 1
        _assert_claim_data_model(
            stability_pool,
            stab_assets,
            claim_assets,
            expected_pairs,
            expected_active,
            expected_num_assets,
        )


def test_claim_data_model_tracks_redemption_reduction_and_green_addition(
    stability_pool,
    alpha_token,
    charlie_token,
    alpha_token_whale,
    charlie_token_whale,
    governance,
    bob,
    alice,
    whale,
    teller,
    auction_house,
    vault_book,
    mock_price_source,
    green_token,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    _seed_stability_asset(
        stability_pool,
        charlie_token,
        charlie_token_whale,
        bob,
        teller,
        mock_price_source,
        100 * 10**6,
    )

    pair_amount = 3 * 10**17
    claim = _deploy_claim_token(
        governance,
        alice,
        700,
        2 * pair_amount,
    )
    setAssetConfig(claim)
    mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)
    for stab_asset in (alpha_token, charlie_token):
        _record_claim(
            stability_pool,
            stab_asset,
            claim,
            alice,
            pair_amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )

    stab_assets = [alpha_token, charlie_token]
    claim_assets = [claim, green_token]
    alpha_address = _asset_address(alpha_token)
    charlie_address = _asset_address(charlie_token)
    expected_pairs = {
        _claim_pair(alpha_token, claim): pair_amount,
        _claim_pair(charlie_token, claim): pair_amount,
    }
    expected_active = {
        alpha_address: [claim],
        charlie_address: [claim],
    }
    expected_num_assets = {
        alpha_address: 2,
        charlie_address: 2,
    }
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    vault_id = vault_book.getRegId(stability_pool)
    first_redemption = 4 * 10**17
    green_token.transfer(bob, first_redemption, sender=whale)
    green_token.approve(teller, first_redemption, sender=bob)
    assert redeem_from_stability_pool(teller,
        vault_id,
        claim,
        first_redemption,
        bob,
        sender=bob,
    ) == first_redemption

    expected_pairs.update(
        {
            _claim_pair(alpha_token, claim): 0,
            _claim_pair(alpha_token, green_token): pair_amount,
            _claim_pair(charlie_token, claim): 2 * 10**17,
            _claim_pair(charlie_token, green_token): 10**17,
        }
    )
    expected_active[alpha_address] = [green_token]
    expected_active[charlie_address] = [claim, green_token]
    expected_num_assets[charlie_address] = 3
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # The second redemption dusts the remaining claim pair while the active
    # GREEN pair receives the entire additional payment.
    second_redemption = 16 * 10**16
    green_token.transfer(bob, second_redemption, sender=whale)
    green_token.approve(teller, second_redemption, sender=bob)
    assert redeem_from_stability_pool(teller,
        vault_id,
        claim,
        second_redemption,
        bob,
        sender=bob,
    ) == second_redemption

    expected_pairs.update(
        {
            _claim_pair(charlie_token, claim): 4 * 10**16,
            _claim_pair(charlie_token, green_token): 26 * 10**16,
        }
    )
    expected_active[charlie_address] = [claim, green_token]
    expected_num_assets[charlie_address] = 3
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )


############################################################################
# WP1 (Section 8.3/8.4): StabilityPool custody and price characterization
#
# Written against the bound RH baseline before any owner disposition of
# RH-CHANGE-01. Plain PASSING tests pin the exact behavior that exists today;
# strict-xfail tests are the Section 6.1(B) preserved checkpoints stating the
# invariant the plan wants (SP-1, SP-6).
############################################################################


def test_direct_stability_pool_primitive_relies_on_auctionhouse_receipt_delta(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """DV-08 composition boundary (SV-1, SP-6).

    StabVault._addClaimableBalance validates a settlement receipt against the
    *aggregate* free surplus `custody - totalClaimableBalances`, not against a
    delta measured across this transaction. Donating D up front and then
    settling a liquidation that declares Q while transferring only Q - D leaves
    the free surplus at exactly Q, so the short receipt is accepted and the
    donation is silently consumed as liquidation proceeds when this unit test
    impersonates AuctionHouse and calls the pool primitive directly.

    Production liquidation does not expose that sequence: the authenticated
    AuctionHouse measures the pool's claim-token balance immediately before and
    after its collateral transfer and reverts unless the exact declared amount
    arrived.  The cross-contract regression lives in
    test_ah_liq_stab.py::test_stability_swap_rejects_donation_masked_short_receipt_from_shares_vault.
    """
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    declared = 10 * EIGHTEEN_DECIMALS
    donation = 3 * EIGHTEEN_DECIMALS
    actually_sent = declared - donation

    # Step 1: an unrelated party donates directly to the pool.
    bravo_token.transfer(stability_pool, donation, sender=bravo_token_whale)
    assert stability_pool.totalClaimableBalances(bravo_token) == 0
    assert bravo_token.balanceOf(stability_pool) == donation

    # Step 2: the authenticated AuctionHouse settles short ...
    bravo_token.transfer(stability_pool, actually_sent, sender=bravo_token_whale)
    # Step 3: ... but declares the full amount.
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        declared,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    # The declared amount was recorded even though only `actually_sent` arrived
    # for this settlement. Custody exactly equals the recorded liability, so no
    # later check can tell that the donation was consumed.
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == declared
    assert stability_pool.totalClaimableBalances(bravo_token) == declared
    assert bravo_token.balanceOf(stability_pool) == declared


def test_short_stability_receipt_without_donation_still_reverts(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """DV-08 boundary: the existing aggregate guard works without a donation."""
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    declared = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, declared - 1, sender=bravo_token_whale)
    before = _stab_state_snapshot(stability_pool, alpha_token, [bravo_token], [bob])

    with boa.reverts("short claim receipt"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            1,
            bravo_token,
            declared,
            ZERO_ADDRESS,
            alpha_token,
            savings_green,
            sender=auction_house.address,
        )

    # Section 8.4: full atomic rollback of custody, shares, indexes, cap usage,
    # and claim data -- not just the two liability mappings.
    assert _stab_state_snapshot(stability_pool, alpha_token, [bravo_token], [bob]) == before
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0


def test_active_claim_custody_deficit_fails_closed_for_value_extracting_actions(
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
    green_token,
    savings_green,
):
    """An active aggregate custody deficit freezes every NAV-moving path."""
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        claim_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    )

    value_before = stability_pool.getTotalValue(alpha_token)
    assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
    assert bravo_token.balanceOf(stability_pool) == claim_amount

    # Half the claim custody disappears (rebase/burn class of event).
    burned = claim_amount // 2
    bravo_token.burn(burned, sender=stability_pool.address)

    assert bravo_token.balanceOf(stability_pool) == claim_amount - burned
    # The recorded liability is untouched, but NAV can no longer be trusted.
    assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)

    # A new deposit has already arrived in Teller custody; the vault must reject
    # minting shares against the overstated NAV.
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    shares_before = stability_pool.totalBalances(alpha_token)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
        )
    assert stability_pool.totalBalances(alpha_token) == shares_before
    assert stability_pool.userBalances(alice, alpha_token) == 0

    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address
        )
    assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
    assert bravo_token.balanceOf(stability_pool) < stability_pool.totalClaimableBalances(
        bravo_token
    )
    assert value_before > 0


@pytest.mark.parametrize(
    ("reserved", "claim_state"),
    (
        (20 * EIGHTEEN_DECIMALS, CLAIM_ASSET_ACTIVE),
        (ACTIVATION_THRESHOLD - 1, CLAIM_ASSET_DORMANT),
    ),
    ids=("active_claim", "dormant_claim"),
)
def test_claim_reserve_cannot_be_reclassified_as_stability_backing(
    reserved,
    claim_state,
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
    green_token,
    savings_green,
):
    """A claim token cannot later be admitted as a stability asset.

    Alpha's cohort owns either an active or a sub-threshold dormant BRAVO
    claim. A later BRAVO deposit is also the vault's attempted admission of
    BRAVO as a stability asset; it must fail before shares can classify any of
    the claim-reserved custody as backing. The dormant row proves admission is
    gated by aggregate liability rather than only by the active-claim index.
    """
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        reserved,
        bob,
        auction_house,
        green_token,
        savings_green,
    )

    assert stability_pool.totalClaimableBalances(bravo_token) == reserved
    assert bravo_token.balanceOf(stability_pool) == reserved
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == claim_state
    assert not stability_pool.isSupportedVaultAsset(bravo_token)

    attempted_deposit = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(
        stability_pool,
        attempted_deposit,
        sender=bravo_token_whale,
    )
    with boa.reverts("asset reserved for claims"):
        stability_pool.depositTokensInVault(
            alice,
            bravo_token,
            attempted_deposit,
            sender=teller.address,
        )

    assert not stability_pool.isSupportedVaultAsset(bravo_token)
    assert stability_pool.totalBalances(bravo_token) == 0
    assert stability_pool.userBalances(alice, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == reserved
    assert bravo_token.balanceOf(stability_pool) == reserved + attempted_deposit

    # Alice never receives BRAVO shares and therefore cannot withdraw Alpha's
    # reserved claim custody (or the unallocated attempted deposit).
    with boa.reverts("user has no shares"):
        stability_pool.withdrawTokensFromVault(
            alice,
            bravo_token,
            MAX_UINT256,
            alice,
            sender=teller.address,
        )
    assert bravo_token.balanceOf(stability_pool) == reserved + attempted_deposit
    assert stability_pool.totalClaimableBalances(bravo_token) == reserved


# --------------------------------------------------------------------------
# DV-09 hardening checkpoints, one independently executing node per action
# --------------------------------------------------------------------------


def _stab_state_snapshot(pool, stab_asset, claim_assets, users, include_values=True):
    """Complete observable StabilityPool state.

    Covers everything Section 8.4 requires to be unchanged after a failed
    operation: stab and claim custody, global and per-user shares, the
    claim-asset registry (arrays, indexes, active count), recorded liabilities,
    per-pair claim data, and reported value.
    """
    state = {
        "stab_custody": stab_asset.balanceOf(pool.address),
        "total_shares": pool.totalBalances(stab_asset),
        "num_vault_assets": pool.numAssets(),
        "num_claimable_assets": pool.numClaimableAssets(stab_asset),
        "num_active_claim_assets": pool.getNumActiveClaimAssets(stab_asset),
        "is_paused": pool.isPaused(),
        "total_value": pool.getTotalValue(stab_asset) if include_values else None,
    }
    for claim in claim_assets:
        state[("claim", _asset_address(claim))] = (
            claim.balanceOf(pool.address),
            pool.claimableBalances(stab_asset, claim),
            pool.totalClaimableBalances(claim),
            pool.indexOfClaimableAsset(stab_asset, claim),
            pool.getClaimAssetState(stab_asset, claim),
        )
    for i in range(1, MAX_ACTIVE_CLAIM_ASSETS + 1):
        state[("claim_slot", i)] = pool.claimableAssets(stab_asset, i)
    for user in users:
        state[("user", user)] = (
            pool.userBalances(user, stab_asset),
            pool.getTotalUserValue(user, stab_asset) if include_values else None,
            pool.numUserAssets(user),
            pool.indexOfUserAsset(user, stab_asset),
            stab_asset.balanceOf(user),
        )
    return state


@pytest.fixture
def deficit_pool(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """A pool whose recorded claim liability exceeds real claim custody.

    Half the bravo claim custody is burned after activation, leaving
    totalClaimableBalances above balanceOf. Returns the recorded claim amount.
    """
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, claim_amount,
        bob, auction_house, green_token, savings_green,
    )
    bravo_token.burn(claim_amount // 2, sender=stability_pool.address)
    assert bravo_token.balanceOf(stability_pool) < stability_pool.totalClaimableBalances(
        bravo_token
    )
    return claim_amount


def test_active_claim_custody_deficit_blocks_deposit(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bob, alice,
    teller, deficit_pool,
):
    """DV-09 hardening target, deposit half (SP-1, Section 11.1)."""
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    before = _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob, alice], False
    )
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
        )
    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob, alice], False
    ) == before


def test_active_claim_custody_deficit_blocks_withdrawal(
    stability_pool, alpha_token, bravo_token, bob, teller, deficit_pool,
):
    """DV-09 hardening target, withdrawal half (SP-1, Section 11.1)."""
    before = _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    )
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address
        )
    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    ) == before


def test_active_claim_custody_deficit_blocks_total_value(
    stability_pool, alpha_token, deficit_pool,
):
    """DV-09 hardening target, valuation half (SP-1, Section 11.1).

    Section 11.1 lists total pool value first: NAV must not keep valuing a
    liability the pool cannot honour.
    """
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)


def test_active_claim_custody_deficit_is_repaired_by_replenishment(
    stability_pool, alpha_token, bravo_token, bravo_token_whale, bob, alice,
    alpha_token_whale, teller, deficit_pool,
):
    """Section 11.1 repair half: direct replenishment restores normal operation.

    A repair action may proceed only if it cannot worsen another user's
    position. Replenishing the missing custody leaves every recorded liability
    and every user's share balance untouched, and normal operations resume.
    """
    missing = stability_pool.totalClaimableBalances(bravo_token) - bravo_token.balanceOf(
        stability_pool.address
    )
    assert missing > 0
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )
    liability_before = stability_pool.totalClaimableBalances(bravo_token)
    pair_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    bob_shares_before = stability_pool.userBalances(bob, alpha_token)

    bravo_token.transfer(stability_pool, missing, sender=bravo_token_whale)

    assert bravo_token.balanceOf(stability_pool) == liability_before
    assert stability_pool.totalClaimableBalances(bravo_token) == liability_before
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair_before
    assert stability_pool.userBalances(bob, alpha_token) == bob_shares_before
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1)[1] != 0

    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
    ) == EIGHTEEN_DECIMALS


############################################################################
# WP1 (Section 8.4): StabilityPool token and custody matrix
#
# Every token behavior is an independently parametrized node. Two return-shape
# doubles are declared inline because no repository mock produces them; per
# Section 3.3 they are the smallest way to exercise the real contract path and
# are deliberately not a framework.
############################################################################

# transfer(address,uint256) with no return data at all. Vyper's
# default_return_value=True is supposed to accept this shape.
NO_RETURN_TOKEN_SOURCE = """
# @version 0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

name: public(constant(String[32])) = "No Return Token"
symbol: public(constant(String[32])) = "NORET"
decimals: public(constant(uint8)) = 18
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

@deploy
def __init__(_holder: address, _supply: uint256):
    self.balanceOf[_holder] = _supply
    self.totalSupply = _supply

@external
def mint(_to: address, _value: uint256):
    self.balanceOf[_to] += _value
    self.totalSupply += _value

@external
def transfer(_to: address, _value: uint256):
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)

@external
def transferFrom(_from: address, _to: address, _value: uint256):
    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True
"""

# transfer(address,uint256) returning 64 bytes -- trailing/malformed return
# data for a caller that expects a single bool.
WIDE_RETURN_TOKEN_SOURCE = """
# @version 0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

name: public(constant(String[32])) = "Wide Return Token"
symbol: public(constant(String[32])) = "WIDE"
decimals: public(constant(uint8)) = 18
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

@deploy
def __init__(_holder: address, _supply: uint256):
    self.balanceOf[_holder] = _supply
    self.totalSupply = _supply

@external
def mint(_to: address, _value: uint256):
    self.balanceOf[_to] += _value
    self.totalSupply += _value

@external
def transfer(_to: address, _value: uint256) -> (bool, bool):
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True, True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> (bool, bool):
    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True, True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True
"""


def _no_return_token(holder, supply):
    return boa.loads(
        NO_RETURN_TOKEN_SOURCE,
        holder,
        supply,
        name="no_return_claim_token",
        override_address=boa.env.generate_address(),
    )


def _wide_return_token(holder, supply):
    return boa.loads(
        WIDE_RETURN_TOKEN_SOURCE,
        holder,
        supply,
        name="wide_return_claim_token",
        override_address=boa.env.generate_address(),
    )


# ---- inbound settlement matrix -------------------------------------------


def test_inbound_exact_settlement_records_exactly(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
):
    """Section 8.4 row 1: exact transfer."""
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    declared = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, declared,
        bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == declared
    assert stability_pool.totalClaimableBalances(bravo_token) == declared
    assert bravo_token.balanceOf(stability_pool) == declared


def test_inbound_donation_plus_exact_settlement_leaves_donation_unallocated(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
):
    """Section 8.4 row 2: pre-existing donation plus an exact transfer.

    The donation must remain unallocated surplus -- custody above recorded
    liability -- and must not be credited as liquidation receipt.
    """
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    donation = 3 * EIGHTEEN_DECIMALS
    declared = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, donation, sender=bravo_token_whale)

    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, declared,
        bob, auction_house, green_token, savings_green,
    )

    assert stability_pool.claimableBalances(alpha_token, bravo_token) == declared
    assert stability_pool.totalClaimableBalances(bravo_token) == declared
    # Surplus is retained, not credited.
    assert bravo_token.balanceOf(stability_pool) == declared + donation


def test_inbound_fee_on_transfer_settlement_reverts_atomically(
    stability_pool, alpha_token, alpha_token_whale, bob, governance, teller,
    auction_house, mock_price_source, savings_green,
):
    """Section 8.4 row 4: inbound fee.

    AuctionHouse declares the gross amount but a fee-on-transfer claim token
    delivers less, so the aggregate free-surplus guard fires and the whole
    settlement rolls back.
    """
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source
    )
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance,
        5_00,  # 5% transfer fee
        name="fee_claim_token",
        override_address=boa.env.generate_address(),
    )
    mock_price_source.setPrice(fee_token, EIGHTEEN_DECIMALS)

    declared = 10 * EIGHTEEN_DECIMALS
    fee_token.transfer(stability_pool, declared, sender=governance.address)
    assert fee_token.balanceOf(stability_pool) < declared

    before = _stab_state_snapshot(stability_pool, alpha_token, [fee_token], [bob])
    with boa.reverts("short claim receipt"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token, 1, fee_token, declared, ZERO_ADDRESS, alpha_token,
            savings_green, sender=auction_house.address,
        )
    assert _stab_state_snapshot(stability_pool, alpha_token, [fee_token], [bob]) == before


def test_upward_rebase_after_activation_is_not_credited_to_claim_liability(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
):
    """Section 8.4 row 6: upward rebase after activation.

    Extra custody arriving after activation is surplus: it must not inflate the
    recorded liability or the pool's reported value.
    """
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    declared = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, declared,
        bob, auction_house, green_token, savings_green,
    )
    value_before = stability_pool.getTotalValue(alpha_token)

    bravo_token.transfer(stability_pool, 5 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)

    assert stability_pool.claimableBalances(alpha_token, bravo_token) == declared
    assert stability_pool.totalClaimableBalances(bravo_token) == declared
    assert stability_pool.getTotalValue(alpha_token) == value_before


# ---- outbound claim-delivery matrix ---------------------------------------


def _setup_outbound_claim(
    stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
    mock_price_source, savings_green, setGeneralConfig, setAssetConfig, vault_book,
    claim_token, claim_holder, declared,
):
    """Seed a pool and record `declared` of `claim_token` as claimable."""
    setGeneralConfig()
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, 100 * EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(claim_token, EIGHTEEN_DECIMALS)
    setAssetConfig(claim_token)
    claim_token.transfer(stability_pool, declared, sender=claim_holder)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, claim_token, declared, ZERO_ADDRESS, alpha_token,
        savings_green, sender=auction_house.address,
    )
    assert stability_pool.claimableBalances(alpha_token, claim_token) == declared
    return vault_book.getRegId(stability_pool)


def test_outbound_exact_delivery_reduces_liability_exactly(
    stability_pool, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, savings_green,
    setGeneralConfig, setAssetConfig, vault_book,
):
    """Section 8.4 outbound row 1: exact transfer out."""
    declared = 10 * EIGHTEEN_DECIMALS
    vault_id = _setup_outbound_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
        mock_price_source, savings_green, setGeneralConfig, setAssetConfig,
        vault_book, bravo_token, bravo_token_whale, declared,
    )
    recipient_before = bravo_token.balanceOf(bob)

    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    delivered = bravo_token.balanceOf(bob) - recipient_before
    assert delivered == declared
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0


@pytest.mark.parametrize("failure_mode", ("return_false", "revert"))
def test_outbound_failing_delivery_rolls_back_the_whole_claim(
    failure_mode,
    stability_pool, alpha_token, alpha_token_whale, bob, governance, teller,
    auction_house, mock_price_source, savings_green, setGeneralConfig,
    setAssetConfig, vault_book,
):
    """Section 8.4 outbound rows: false return and revert.

    SP-4: a failed outbound transfer must roll the share burn back completely.
    """
    declared = 10 * EIGHTEEN_DECIMALS
    probe = boa.load(
        "contracts/mock/MockProbeErc20.vy",
        governance,
        1_000 * EIGHTEEN_DECIMALS,
        name=f"probe_claim_token_{failure_mode}",
        override_address=boa.env.generate_address(),
    )
    vault_id = _setup_outbound_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
        mock_price_source, savings_green, setGeneralConfig, setAssetConfig,
        vault_book, probe, governance.address, declared,
    )

    if failure_mode == "return_false":
        probe.setReturnFalse(True, sender=governance.address)
    else:
        probe.setRevertTransfers(True, sender=governance.address)

    before = _stab_state_snapshot(stability_pool, alpha_token, [probe], [bob])
    with boa.reverts():
        claim_from_stability_pool(teller, vault_id, alpha_token, probe, sender=bob)
    assert _stab_state_snapshot(stability_pool, alpha_token, [probe], [bob]) == before


@pytest.mark.parametrize("return_shape", ("no_return_data", "wide_return_data"))
def test_outbound_nonstandard_return_shape_delivery(
    return_shape,
    stability_pool, alpha_token, alpha_token_whale, bob, governance, teller,
    auction_house, mock_price_source, savings_green, setGeneralConfig,
    setAssetConfig, vault_book,
):
    """Section 8.4 outbound rows: no return data and trailing return data.

    Characterizes the exact bound behavior rather than asserting a policy.
    Measured on the bound tree: Vyper's `default_return_value=True` accepts an
    empty return, and a 64-byte return for a bool-typed call is *also* accepted
    -- the decoder reads the first word and does not reject the trailing data.
    Both shapes therefore deliver normally. The protocol does not fail closed on
    non-canonical return data; it simply is not misled by it (SP-6).
    """
    declared = 10 * EIGHTEEN_DECIMALS
    supply = 1_000 * EIGHTEEN_DECIMALS
    token = (
        _no_return_token(governance.address, supply)
        if return_shape == "no_return_data"
        else _wide_return_token(governance.address, supply)
    )
    vault_id = _setup_outbound_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
        mock_price_source, savings_green, setGeneralConfig, setAssetConfig,
        vault_book, token, governance.address, declared,
    )
    before = _stab_state_snapshot(stability_pool, alpha_token, [token], [bob])
    recipient_before = token.balanceOf(bob)

    claim_from_stability_pool(teller, vault_id, alpha_token, token, sender=bob)

    # Both shapes deliver the exact amount and clear the liability exactly, so
    # no phantom value is created and no deficit is concealed.
    assert token.balanceOf(bob) - recipient_before == declared
    assert stability_pool.claimableBalances(alpha_token, token) == 0
    assert stability_pool.totalClaimableBalances(token) == 0
    assert token.balanceOf(stability_pool.address) == 0
    assert before[("claim", _asset_address(token))][1] == declared


def test_outbound_fee_on_transfer_short_delivery_reverts_atomically(
    stability_pool, alpha_token, alpha_token_whale, bob, governance, teller,
    auction_house, mock_price_source, savings_green, setGeneralConfig,
    setAssetConfig, vault_book,
):
    """A fee-on-transfer claim cannot burn shares or recorded liability."""
    declared = 10 * EIGHTEEN_DECIMALS
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance,
        0,  # no fee during settlement, so the receipt guard is satisfied
        name="outbound_fee_claim_token",
        override_address=boa.env.generate_address(),
    )
    vault_id = _setup_outbound_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
        mock_price_source, savings_green, setGeneralConfig, setAssetConfig,
        vault_book, fee_token, governance.address, declared,
    )

    # Turn the fee on only for the outbound leg.
    fee_token.setTransferFee(5_00, sender=governance.address)
    before = _stab_state_snapshot(stability_pool, alpha_token, [fee_token], [bob])

    with boa.reverts():
        claim_from_stability_pool(teller, vault_id, alpha_token, fee_token, sender=bob)
    assert _stab_state_snapshot(stability_pool, alpha_token, [fee_token], [bob]) == before


def test_outbound_fee_on_transfer_stability_asset_does_not_burn_shares(
    stability_pool, governance, bob, teller, mock_price_source,
):
    """The exact-delivery invariant also covers ordinary pool withdrawals."""
    amount = 100 * EIGHTEEN_DECIMALS
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance,
        0,
        name="fee_stability_asset",
        override_address=boa.env.generate_address(),
    )
    _seed_stability_asset(
        stability_pool, fee_token, governance.address, bob, teller,
        mock_price_source, amount,
    )
    fee_token.setTransferFee(5_00, sender=governance.address)
    before = (
        fee_token.balanceOf(stability_pool),
        fee_token.balanceOf(bob),
        stability_pool.userBalances(bob, fee_token),
        stability_pool.totalBalances(fee_token),
    )

    with boa.reverts():
        stability_pool.withdrawTokensFromVault(
            bob, fee_token, amount, bob, sender=teller.address
        )

    assert (
        fee_token.balanceOf(stability_pool),
        fee_token.balanceOf(bob),
        stability_pool.userBalances(bob, fee_token),
        stability_pool.totalBalances(fee_token),
    ) == before


############################################################################
# WP5 (Section 12.1) / DV-14: the PriceDesk boundary, per price state
#
# SP-PRICE-01 is option A on the bound baseline, so these are characterizations
# of the exact result each price state produces. PriceDesk now isolates source
# failures: strict NAV calls still fail closed without a healthy fallback,
# while non-strict maintenance sees zero and leaves the priceless asset active.
############################################################################

# (price state, applies it, expected NAV outcome on the bound tree)
PRICE_STATES = ("valid", "zero", "absent_feed", "source_revert")


def _apply_price_state(mock_price_source, asset, state):
    if state == "valid":
        mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    elif state == "zero":
        mock_price_source.setPrice(asset, 0)
    elif state == "absent_feed":
        mock_price_source.disablePriceFeed(asset)
    elif state == "source_revert":
        mock_price_source.setShouldRevert(asset, True)
    else:  # pragma: no cover
        raise AssertionError(state)


def _restore_price_state(mock_price_source, asset):
    mock_price_source.setShouldRevert(asset, False)
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)


@pytest.fixture
def priced_claim_pool(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    setGeneralConfig, setAssetConfig,
):
    """100 alpha deposited by bob, 20 bravo recorded as an active claim asset."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, 100 * EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 20 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, claim_amount,
        bob, auction_house, green_token, savings_green,
    )
    return claim_amount


@pytest.mark.parametrize("state", PRICE_STATES)
def test_claim_asset_price_state_nav_outcome(
    state, stability_pool, alpha_token, bravo_token, bob, mock_price_source,
    priced_claim_pool,
):
    """Every unavailable-price state fails closed while a claim is active."""
    priced_nav = stability_pool.getTotalValue(alpha_token)
    stab_custody = alpha_token.balanceOf(stability_pool.address)
    assert priced_nav == stab_custody + priced_claim_pool
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    healthy_position = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)
    assert healthy_position[0] == alpha_token.address
    assert healthy_position[1] == stability_pool.getTotalAmountForUser(
        bob,
        alpha_token,
    )
    state_before = (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        alpha_token.balanceOf(stability_pool),
        bravo_token.balanceOf(stability_pool),
    )

    _apply_price_state(mock_price_source, bravo_token, state)

    if state == "valid":
        assert stability_pool.getTotalValue(alpha_token) == priced_nav
        assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
        assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == healthy_position
    else:
        with boa.reverts():
            stability_pool.getTotalValue(alpha_token)
        assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
        assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
            alpha_token.address,
            0,
        )

    assert (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        alpha_token.balanceOf(stability_pool),
        bravo_token.balanceOf(stability_pool),
    ) == state_before

    if state != "valid":
        _restore_price_state(mock_price_source, bravo_token)
        assert stability_pool.getTotalValue(alpha_token) == priced_nav
        assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
        assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == healthy_position


def test_paused_cohort_is_skipped_without_hiding_nominal_position(
    stability_pool,
    alpha_token,
    bravo_token,
    bob,
    switchboard_alpha,
    priced_claim_pool,
):
    healthy_position = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)
    assert healthy_position[0] == alpha_token.address
    assert healthy_position[1] != 0
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAtIndexAndHasBalance(bob, 1) == (
        alpha_token.address,
        True,
    )

    stability_pool.pause(True, sender=switchboard_alpha.address)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )
    assert stability_pool.getUserAssetAtIndexAndHasBalance(bob, 1) == (
        alpha_token.address,
        True,
    )

    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == healthy_position


def test_empty_registered_cohort_accepts_first_liquidation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    amount = 100 * EIGHTEEN_DECIMALS
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        amount,
    )
    assert stability_pool.withdrawTokensFromVault(
        bob,
        alpha_token,
        amount,
        bob,
        sender=teller.address,
    )[0] == amount
    assert stability_pool.isSupportedVaultAsset(alpha_token)
    assert stability_pool.totalBalances(alpha_token) == 0
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)

    # The empty-cohort exception must not expose raw custody reserved for a
    # different cohort to AuctionHouse sizing.
    alpha_token.transfer(stability_pool, 1, sender=alpha_token_whale)
    stability_pool.eval(
        f"stabVault.totalClaimableBalances[{alpha_token.address}] = 1"
    )
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    stability_pool.eval(
        f"stabVault.totalClaimableBalances[{alpha_token.address}] = 0"
    )
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)


def test_claim_only_cohort_with_unpriceable_stab_asset_is_skipped_and_recovers(
    stability_pool,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    stab_amount = 10 * EIGHTEEN_DECIMALS
    claim_amount = 2 * EIGHTEEN_DECIMALS
    stab_token = _deploy_claim_token(
        governance,
        alpha_token_whale,
        9_901,
        stab_amount + 1,
    )
    setGeneralConfig()
    setAssetConfig(stab_token)
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool,
        stab_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        stab_amount,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert _record_claim(
        stability_pool,
        stab_token,
        bravo_token,
        bravo_token_whale,
        claim_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
        stab_amount=stab_amount,
    ) == stab_amount
    assert stab_token.balanceOf(stability_pool) == 0

    # getTotalValue does not need the stabilization-asset price when there is
    # no unreserved custody, while the phase-2 amount conversion does. This is
    # the exact residual path identified in review.
    mock_price_source.setPrice(stab_token, 0)
    assert stability_pool.getTotalValue(stab_token) == claim_amount
    with boa.reverts():
        stability_pool.getTotalAmountForUser(bob, stab_token)
    assert not stability_pool.canAcceptLiquidationAsset(stab_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        stab_token.address,
        0,
    )

    # Restoring both priceability and transferable custody makes the cohort
    # usable without changing claim/share accounting.
    _restore_price_state(mock_price_source, stab_token)
    stab_token.transfer(stability_pool, 1, sender=alpha_token_whale)
    assert stability_pool.canAcceptLiquidationAsset(stab_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1)[1] != 0


def test_fully_reserved_stab_custody_is_skipped_before_collateral_can_move(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
        10 * EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 2 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        claim_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    )

    # Current deposits forbid this overlap, but migrated/legacy state can carry
    # cross-cohort liabilities in the same token. Model that state directly:
    # raw balanceOf is nonzero, yet every unit is reserved elsewhere.
    reserved = alpha_token.balanceOf(stability_pool)
    stability_pool.eval(
        f"stabVault.totalClaimableBalances[{alpha_token.address}] = {reserved}"
    )
    assert stability_pool.getTotalValue(alpha_token) == claim_amount
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )

    stability_pool.eval(
        f"stabVault.totalClaimableBalances[{alpha_token.address}] = 0"
    )
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1)[1] != 0


def test_production_liquidation_preflight_uses_typed_pricedesk_boundary():
    source = (ROOT / "contracts/vaults/modules/StabVault.vy").read_text()
    start = source.index("def _getCohortLiquidationAmount")
    end = source.index("def _getUserAssetAndAmountAtIndex", start)
    helper = source[start:end]

    assert "raw_call(" not in helper
    assert "staticcall IERC20(" in helper
    assert "self._getUsdValue(" in helper
    assert "custody <= reserved" in helper
    assert "claimableValue += claimValue" in helper

    start = source.index("def _getUserAssetAndAmountAtIndex")
    end = source.index("def _getUserAssetAtIndexAndHasBalance", start)
    iterator = source[start:end]
    assert "self._getCohortLiquidationAmount(asset)" in iterator
    assert "self._getTotalAmountForUser(" not in iterator


@pytest.mark.parametrize(
    "action", ("total_value", "user_value", "deposit", "withdraw", "claim", "prune")
)
def test_reverting_price_source_takes_down_every_nav_dependent_action(
    action, stability_pool, alpha_token, bravo_token, alpha_token_whale, bob, alice,
    teller, mock_price_source, vault_book, priced_claim_pool,
):
    """DV-14 characterization (SP-3, Section 12.1) across the affected methods.

    Without a healthy fallback, strict NAV paths still fail closed. Non-strict
    pruning no longer propagates the source revert, but it cannot remove the
    active asset because the isolated lookup returns zero.
    """
    vault_id = vault_book.getRegId(stability_pool)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    mock_price_source.setShouldRevert(bravo_token, True)

    if action == "prune":
        active_index = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
        stability_pool.pruneClaimableAssets(
            alpha_token,
            [bravo_token],
            sender=alice,
        )
        assert stability_pool.indexOfClaimableAsset(
            alpha_token,
            bravo_token,
        ) == active_index
        return

    with boa.reverts():
        if action == "total_value":
            stability_pool.getTotalValue(alpha_token)
        elif action == "user_value":
            stability_pool.getTotalUserValue(bob, alpha_token)
        elif action == "deposit":
            stability_pool.depositTokensInVault(
                alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
            )
        elif action == "withdraw":
            stability_pool.withdrawTokensFromVault(
                bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address
            )
        else:
            claim_from_stability_pool(
                teller, vault_id, alpha_token, bravo_token, sender=bob
            )


def test_reverting_price_source_is_fully_atomic_and_recovers(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bob, alice, teller,
    mock_price_source, priced_claim_pool,
):
    """Section 12.2: a source failure must leave no partial state behind."""
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    before = _stab_state_snapshot(stability_pool, alpha_token, [bravo_token], [bob, alice])

    mock_price_source.setShouldRevert(bravo_token, True)
    with boa.reverts():
        stability_pool.depositTokensInVault(
            alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
        )
    mock_price_source.setShouldRevert(bravo_token, False)

    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob, alice]
    ) == before
    # Normal operation resumes once the source recovers.
    assert stability_pool.depositTokensInVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
    ) == EIGHTEEN_DECIMALS


def test_reverting_priority_source_with_healthy_fallback_keeps_stability_live(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, alice, teller,
    price_desk, governance, mission_control, switchboard_alpha, priced_claim_pool,
    mock_price_source,
):
    failed = boa.load(
        "contracts/mock/MockRawPriceSource.vy",
        name="stab_reverting_price_source",
    )
    failed.configure(0, True, 1, 0, 0)

    assert price_desk.startAddNewAddressToRegistry(
        failed,
        "reverting priority",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    failed_id = price_desk.confirmNewAddressToRegistry(
        failed,
        sender=governance.address,
    )
    healthy_id = price_desk.getRegId(mock_price_source)
    assert healthy_id != 0
    mission_control.setPriorityPriceSourceIds(
        [failed_id, healthy_id],
        sender=switchboard_alpha.address,
    )

    alpha_token.transfer(
        stability_pool,
        EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    assert stability_pool.depositTokensInVault(
        alice,
        alpha_token,
        EIGHTEEN_DECIMALS,
        sender=teller.address,
    ) == EIGHTEEN_DECIMALS
    assert stability_pool.getTotalValue(alpha_token) != 0


@pytest.mark.parametrize("state", ("zero", "absent_feed", "source_revert"))
@pytest.mark.parametrize("action", ("deposit", "withdraw"))
def test_unavailable_claim_price_blocks_deposits_and_withdrawals(
    state, action, stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bob, alice, teller, mock_price_source, priced_claim_pool,
):
    """Cohort shares cannot move while an active claim cannot be priced."""
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    _apply_price_state(mock_price_source, bravo_token, state)

    with boa.reverts():
        if action == "deposit":
            stability_pool.depositTokensInVault(
                alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address
            )
        else:
            stability_pool.withdrawTokensFromVault(
                bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address
            )


# ---- Section 8.3 remaining zero-price transitions -------------------------


@pytest.mark.parametrize("portion", ("partial", "full"))
def test_withdrawal_during_zero_price_outage_reverts_without_abandoning_claims(
    portion, stability_pool, alpha_token, bravo_token, alpha_token_whale, bob,
    teller, mock_price_source, priced_claim_pool,
):
    """Partial and full exits fail closed until the active claim is priced."""
    stab_custody = alpha_token.balanceOf(stability_pool.address)

    mock_price_source.setPrice(bravo_token, 0)
    amount = stab_custody if portion == "full" else stab_custody // 4
    before = _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    )
    with boa.reverts():
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, amount, bob, sender=teller.address
        )
    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    ) == before


def test_claim_and_redemption_resume_exactly_after_price_restoration(
    stability_pool, alpha_token, bravo_token, bob, teller, mock_price_source,
    vault_book, priced_claim_pool,
):
    """Section 8.3: claim before, during, and after the outage.

    Before the outage the claim works; during it the claim path fails closed
    (its amount resolution uses _shouldRaise=True); after restoration it works
    again and delivers exactly the recorded balance.
    """
    vault_id = vault_book.getRegId(stability_pool)

    # During the outage the claim fails closed and changes nothing.
    mock_price_source.setPrice(bravo_token, 0)
    before = _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    )
    with boa.reverts():
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], False
    ) == before

    # After restoration the claim succeeds and delivers exactly.
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    recipient_before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    assert bravo_token.balanceOf(bob) - recipient_before == priced_claim_pool
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0


def test_zero_price_at_the_maximum_active_claim_asset_count(
    stability_pool, alpha_token, alpha_token_whale, bob, alice, governance, teller,
    auction_house, mock_price_source, green_token, savings_green,
):
    """A zero price at the active cap freezes NAV without mutating the registry."""
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, 100 * EIGHTEEN_DECIMALS + MAX_ACTIVE_CLAIM_ASSETS,
    )
    per_asset = ACTIVATION_THRESHOLD + EIGHTEEN_DECIMALS
    claim_tokens = [
        _deploy_claim_token(governance, alice, 4_100 + i, per_asset)
        for i in range(MAX_ACTIVE_CLAIM_ASSETS)
    ]
    for token in claim_tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, token, alice, per_asset, bob,
            auction_house, green_token, savings_green,
        )
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS

    full_nav = stability_pool.getTotalValue(alpha_token)
    target = claim_tokens[MAX_ACTIVE_CLAIM_ASSETS // 2]
    index_before = stability_pool.indexOfClaimableAsset(alpha_token, target)

    mock_price_source.setPrice(target, 0)

    with boa.reverts():
        stability_pool.getTotalValue(alpha_token)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS
    assert stability_pool.indexOfClaimableAsset(alpha_token, target) == index_before
    assert stability_pool.getClaimAssetState(alpha_token, target) == CLAIM_ASSET_ACTIVE

    mock_price_source.setPrice(target, EIGHTEEN_DECIMALS)
    assert stability_pool.getTotalValue(alpha_token) == full_nav


# ---- Section 11.4: dormant-only dust exit liveness -------------------------


@pytest.mark.parametrize(
    ("label", "dust"),
    (
        ("below_activation", ACTIVATION_THRESHOLD - 1),
        ("at_retention", RETENTION_THRESHOLD),
        ("below_retention", RETENTION_THRESHOLD - 1),
    ),
    ids=("below_activation", "at_retention", "below_retention"),
)
def test_dormant_dust_is_claimable_before_exit_but_stranded_after(
    label, dust, stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, teller, auction_house, mock_price_source, green_token,
    savings_green, vault_book, setGeneralConfig, setAssetConfig,
):
    """DV-15 characterization (SP-5, Section 11.4).

    A below-activation claim balance stays dormant: it is recorded in
    claimableBalances but never enters the iterable active set, so it is
    invisible to NAV. _claimFromStabilityPool reads claimableBalances directly,
    so the holder CAN take it out -- but only while they still hold stability
    shares. A full exit burns those shares, and the dust is then unreachable by
    that user. The pair can return to the active set after a liquidation tops
    it above the activation threshold or, after price appreciation, through
    the paused permissionless ``activateClaimAssets`` maintenance route.
    """
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, 100 * EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, dust, bob,
        auction_house, green_token, savings_green,
    )
    vault_id = vault_book.getRegId(stability_pool)

    # Dormant: recorded, but not active and not in NAV.
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == dust
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.getTotalValue(alpha_token) == alpha_token.balanceOf(
        stability_pool.address
    )

    # While bob still holds shares the dust is reachable.
    with boa.env.anchor():
        recipient_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        assert bravo_token.balanceOf(bob) - recipient_before == dust
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0

    # After a full exit the same dust is stranded.
    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, MAX_UINT256, bob, sender=teller.address
    )
    assert stability_pool.userBalances(bob, alpha_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == dust
    assert bravo_token.balanceOf(stability_pool.address) == dust

    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)


@pytest.mark.xfail(
    strict=True,
    reason="DV-15: post-exit dormant-dust recovery remains absent; accepted risk "
    "under the ratified DER-02 / Section 11.4 / RH-CHANGE-01 monitoring, warning, "
    "and planned-activation policy",
)
def test_dormant_dust_remains_recoverable_after_full_exit(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """DV-15 hardening target (Section 11.4).

    The user must have a defined way to recover every economically owned
    balance without relying on a future liquidation by someone else.
    """
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, 100 * EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    dust = ACTIVATION_THRESHOLD - 1
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale, dust, bob,
        auction_house, green_token, savings_green,
    )
    vault_id = vault_book.getRegId(stability_pool)

    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, MAX_UINT256, bob, sender=teller.address
    )
    recipient_before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert bravo_token.balanceOf(bob) - recipient_before == dust


@pytest.mark.parametrize(
    ("claim_amount", "expected_state"),
    (
        (0, CLAIM_ASSET_ABSENT),
        (1, CLAIM_ASSET_DORMANT),
        (RETENTION_THRESHOLD - 1, CLAIM_ASSET_DORMANT),
        (RETENTION_THRESHOLD, CLAIM_ASSET_DORMANT),
        (RETENTION_THRESHOLD + 1, CLAIM_ASSET_DORMANT),
        (ACTIVATION_THRESHOLD - 1, CLAIM_ASSET_DORMANT),
        (ACTIVATION_THRESHOLD, CLAIM_ASSET_ACTIVE),
        (ACTIVATION_THRESHOLD + 1, CLAIM_ASSET_ACTIVE),
    ),
    ids=(
        "zero",
        "positive-below-retention",
        "immediately-below-retention",
        "exact-retention",
        "between-retention-and-activation",
        "immediately-below-activation",
        "exact-activation",
        "immediately-above-activation",
    ),
)
def test_der02_direct_creation_exit_and_replenishment_partitions(
    claim_amount,
    expected_state,
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
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """Exhaust the finite direct-creation thresholds and their exit polarity.

    Retention is deliberately irrelevant to a directly created inactive pair:
    every positive balance below activation has the same dormant, non-iterable,
    non-NAV state.  Active rows cannot burn the final shares by withdrawing the
    stability asset alone because their claim value remains in NAV.  Dormant
    rows can burn every share and strand the omitted claim. Some threshold
    points intentionally overlap the older dust characterization; this matrix
    adds the full NAV, enumeration, exit, and replenishment state vector.
    """
    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        if claim_amount != 0:
            _record_claim(
                stability_pool,
                alpha_token,
                bravo_token,
                bravo_token_whale,
                claim_amount,
                bob,
                auction_house,
                green_token,
                savings_green,
            )

        vault_id = vault_book.getRegId(stability_pool)
        stab_custody = alpha_token.balanceOf(stability_pool)
        claim_custody = bravo_token.balanceOf(stability_pool)
        shares_before_exit = stability_pool.userBalances(bob, alpha_token)
        total_shares_before_exit = stability_pool.totalBalances(alpha_token)
        expected_active = expected_state == CLAIM_ASSET_ACTIVE

        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == expected_state
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == claim_amount
        assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
        assert claim_custody == claim_amount
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == int(
            expected_active
        )
        claim_index = stability_pool.indexOfClaimableAsset(
            alpha_token, bravo_token
        )
        if expected_active:
            assert claim_index == 1
            assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
        else:
            assert claim_index == 0
            assert stability_pool.claimableAssets(alpha_token, 1) == ZERO_ADDRESS

        expected_nav = stab_custody + (claim_amount if expected_active else 0)
        assert stability_pool.getTotalValue(alpha_token) == expected_nav
        assert abs(
            stability_pool.getTotalUserValue(bob, alpha_token) - expected_nav
        ) <= 1
        assert shares_before_exit == total_shares_before_exit != 0

        # Direct claimability is a share-for-asset exchange, not a free
        # per-user entitlement.  Prove it without consuming the main exit path.
        with boa.env.anchor():
            if claim_amount == 0:
                with boa.reverts("nothing claimed"):
                    claim_from_stability_pool(
                        teller,
                        vault_id,
                        alpha_token,
                        bravo_token,
                        sender=bob,
                    )
            else:
                recipient_before = bravo_token.balanceOf(bob)
                claim_from_stability_pool(
                    teller,
                    vault_id,
                    alpha_token,
                    bravo_token,
                    sender=bob,
                )
                assert bravo_token.balanceOf(bob) - recipient_before == claim_amount
                assert stability_pool.userBalances(
                    bob, alpha_token
                ) < shares_before_exit
        clear_transient_storage()

        withdrawn, depleted = stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            MAX_UINT256,
            bob,
            sender=teller.address,
        )
        assert withdrawn == stab_custody
        assert alpha_token.balanceOf(stability_pool) == 0

        if expected_active:
            # Claim NAV prevents a stability-token-only operation from being a
            # full share exit.  The remaining shares can still claim the asset.
            assert not depleted
            assert stability_pool.userBalances(bob, alpha_token) != 0
            assert stability_pool.totalBalances(alpha_token) != 0
            recipient_before = bravo_token.balanceOf(bob)
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=bob,
            )
            delivered = bravo_token.balanceOf(bob) - recipient_before
            remaining = stability_pool.claimableBalances(alpha_token, bravo_token)
            assert delivered + remaining == claim_amount
            assert remaining == 1
            assert stability_pool.totalClaimableBalances(bravo_token) == remaining
            assert stability_pool.userBalances(bob, alpha_token) == 0
            assert stability_pool.totalBalances(alpha_token) == 0
            assert stability_pool.getClaimAssetState(
                alpha_token, bravo_token
            ) == CLAIM_ASSET_DORMANT
            return

        assert depleted
        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.totalBalances(alpha_token) == 0
        if claim_amount == 0:
            assert stability_pool.getClaimAssetState(
                alpha_token, bravo_token
            ) == CLAIM_ASSET_ABSENT
            return

        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT
        assert bravo_token.balanceOf(stability_pool) == claim_amount
        with boa.reverts("nothing claimed"):
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=bob,
            )
        clear_transient_storage()

        # A later depositor pays only for the currently iterable NAV.  A real
        # later liquidation then tops the pair to activation, at which point
        # that future holder can receive both the new amount and historical
        # residual while the exited holder still cannot.
        future_deposit = 10 * EIGHTEEN_DECIMALS
        alpha_token.transfer(stability_pool, future_deposit, sender=alpha_token_whale)
        assert stability_pool.depositTokensInVault(
            alice,
            alpha_token,
            future_deposit,
            sender=teller.address,
        ) == future_deposit
        top_up = ACTIVATION_THRESHOLD - claim_amount
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            top_up,
            alice,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_ACTIVE
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == ACTIVATION_THRESHOLD
        assert stability_pool.getTotalValue(
            alpha_token
        ) == alpha_token.balanceOf(stability_pool) + ACTIVATION_THRESHOLD
        with boa.reverts("nothing claimed"):
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=bob,
            )
        clear_transient_storage()
        future_recipient_before = bravo_token.balanceOf(alice)
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            sender=alice,
        )
        assert (
            bravo_token.balanceOf(alice) - future_recipient_before
            == ACTIVATION_THRESHOLD
        )


def test_der02_appreciated_post_exit_dormant_pair_uses_paused_activation(
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
    green_token,
    savings_green,
    switchboard_alpha,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """Governance pause plus any caller can recover appreciated dormant dust."""
    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            RETENTION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        vault_id = vault_book.getRegId(stability_pool)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT

        _, depleted = stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            MAX_UINT256,
            bob,
            sender=teller.address,
        )
        assert depleted
        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.totalBalances(alpha_token) == 0
        assert alpha_token.balanceOf(stability_pool) == 0

        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(
            alpha_token, [bravo_token], sender=alice
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT

        mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
        assert stability_pool.getTotalValue(alpha_token) == 0
        stability_pool.activateClaimAssets(
            alpha_token, [bravo_token], sender=alice
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_ACTIVE
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
        assert stability_pool.getTotalValue(alpha_token) == ACTIVATION_THRESHOLD

        stability_pool.pause(False, sender=switchboard_alpha.address)
        future_deposit = 10 * EIGHTEEN_DECIMALS
        alpha_token.transfer(
            stability_pool, future_deposit, sender=alpha_token_whale
        )
        assert stability_pool.depositTokensInVault(
            alice,
            alpha_token,
            future_deposit,
            sender=teller.address,
        ) == future_deposit
        with boa.reverts("nothing claimed"):
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=bob,
            )
        clear_transient_storage()
        recipient_before = bravo_token.balanceOf(alice)
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            sender=alice,
        )
        assert bravo_token.balanceOf(alice) - recipient_before == (
            RETENTION_THRESHOLD
        )


def test_der02_deployment_manifests_bind_recovery_control_and_scope():
    """RH deploys dormant recovery; the older Base pool predates the design."""
    manifest_paths = {
        "robinhood": (
            ROOT
            / "migration_history/robinhood-mainnet/v1/current-manifest.json"
        ),
        "base": ROOT / "migration_history/base-mainnet/v1/current-manifest.json",
    }
    contracts = {
        chain: json.loads(path.read_text())["contracts"]["StabilityPool"]
        for chain, path in manifest_paths.items()
    }
    assert contracts["robinhood"]["address"] == (
        "0xBb18Cc60aFCa88272EdAdb86fc28D56B05e7D46E"
    )
    assert contracts["base"]["address"] == (
        "0x2a157096af6337b2b4bd47de435520572ed5a439"
    )

    recovery_functions = {
        "activateClaimAssets",
        "pruneClaimableAssets",
        "getClaimAssetState",
    }
    function_names = {
        chain: {
            entry["name"]
            for entry in contract["abi"]
            if entry.get("type") == "function"
        }
        for chain, contract in contracts.items()
    }
    assert recovery_functions <= function_names["robinhood"]
    assert recovery_functions.isdisjoint(function_names["base"])

    source_key = "contracts/vaults/modules/StabVault.vy"
    sources = {
        chain: contract["solc_json"]["sources"][source_key]["content"]
        for chain, contract in contracts.items()
    }
    robinhood_markers = (
        "ACTIVATION_USD_THRESHOLD",
        "RETENTION_USD_THRESHOLD",
        "ClaimAssetLeftDormant",
        "def activateClaimAssets(",
        "assert vaultData.isPaused # dev: contract not paused",
    )
    for marker in robinhood_markers:
        assert marker in sources["robinhood"]
        assert marker not in sources["base"]


def test_der02_direct_dormant_claim_value_accrues_to_current_share_cohort(
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
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """Share burn makes a dormant claim economic value pro rata, not personal."""
    dust = ACTIVATION_THRESHOLD - 1

    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            dust,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        vault_id = vault_book.getRegId(stability_pool)
        sole_value_before = stability_pool.getTotalUserValue(bob, alpha_token)
        sole_shares_before = stability_pool.userBalances(bob, alpha_token)
        recipient_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            sender=bob,
        )
        delivered = bravo_token.balanceOf(bob) - recipient_before
        sole_value_after = stability_pool.getTotalUserValue(bob, alpha_token)
        assert delivered == dust
        assert stability_pool.userBalances(
            bob, alpha_token
        ) < sole_shares_before
        assert abs(
            sole_value_after + delivered - sole_value_before - dust
        ) <= 1
    clear_transient_storage()

    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        for user in (bob, alice):
            _seed_stability_asset(
                stability_pool,
                alpha_token,
                alpha_token_whale,
                user,
                teller,
                mock_price_source,
                100 * EIGHTEEN_DECIMALS,
            )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            dust,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        vault_id = vault_book.getRegId(stability_pool)
        bob_value_before = stability_pool.getTotalUserValue(bob, alpha_token)
        alice_value_before = stability_pool.getTotalUserValue(alice, alpha_token)
        bob_shares_before = stability_pool.userBalances(bob, alpha_token)
        recipient_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(
            teller,
            vault_id,
            alpha_token,
            bravo_token,
            sender=bob,
        )
        delivered = bravo_token.balanceOf(bob) - recipient_before
        bob_net = (
            stability_pool.getTotalUserValue(bob, alpha_token)
            + delivered
            - bob_value_before
        )
        peer_gain = (
            stability_pool.getTotalUserValue(alice, alpha_token)
            - alice_value_before
        )
        assert delivered == dust
        assert stability_pool.userBalances(bob, alpha_token) < bob_shares_before
        # Exact committed evidence for this 100/100 alpha, 50/50 cohort. The
        # small asymmetry is second-order dilution, not an arbitrary tolerance.
        assert (bob_net, peer_gain) == (
            49_974_987_493_746_873,
            50_025_012_506_253_126,
        )
        assert bob_net + peer_gain == dust


@pytest.mark.parametrize("first_exiter_name", ("bob", "alice"))
def test_der02_active_to_dormant_multi_holder_exit_orders(
    first_exiter_name,
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
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """An active claim loses NAV on dormancy; neither exit order is paid for it."""
    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        for user in (bob, alice):
            _seed_stability_asset(
                stability_pool,
                alpha_token,
                alpha_token_whale,
                user,
                teller,
                mock_price_source,
                100 * EIGHTEEN_DECIMALS,
            )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        dormant_amount = ACTIVATION_THRESHOLD - 1
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            dormant_amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        vault_id = vault_book.getRegId(stability_pool)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT
        assert stability_pool.getTotalValue(alpha_token) == (
            alpha_token.balanceOf(stability_pool)
        )
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == dormant_amount
        assert stability_pool.totalClaimableBalances(
            bravo_token
        ) == dormant_amount

        users = {"bob": bob, "alice": alice}
        first = users[first_exiter_name]
        second = alice if first == bob else bob
        first_available = stability_pool.getTotalAmountForUser(first, alpha_token)
        first_withdrawn, first_depleted = stability_pool.withdrawTokensFromVault(
            first,
            alpha_token,
            MAX_UINT256,
            first,
            sender=teller.address,
        )
        assert first_withdrawn == first_available
        assert first_depleted
        assert stability_pool.userBalances(first, alpha_token) == 0
        assert stability_pool.userBalances(second, alpha_token) != 0
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == dormant_amount
        with boa.reverts("nothing claimed"):
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=first,
            )
        clear_transient_storage()

        # The remaining holder can still exchange shares for the entire
        # dormant token balance, proving that exit changed the eligible
        # recipient rather than paying the first exiter through NAV.
        with boa.env.anchor():
            recipient_before = bravo_token.balanceOf(second)
            claim_from_stability_pool(
                teller,
                vault_id,
                alpha_token,
                bravo_token,
                sender=second,
            )
            assert (
                bravo_token.balanceOf(second) - recipient_before
                == dormant_amount
            )
        clear_transient_storage()

        second_available = stability_pool.getTotalAmountForUser(second, alpha_token)
        second_withdrawn, second_depleted = stability_pool.withdrawTokensFromVault(
            second,
            alpha_token,
            MAX_UINT256,
            second,
            sender=teller.address,
        )
        assert second_withdrawn == second_available
        assert second_depleted
        assert stability_pool.totalBalances(alpha_token) == 0
        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.userBalances(alice, alpha_token) == 0
        assert bravo_token.balanceOf(stability_pool) == dormant_amount
        for exited in (first, second):
            with boa.reverts("nothing claimed"):
                claim_from_stability_pool(
                    teller,
                    vault_id,
                    alpha_token,
                    bravo_token,
                    sender=exited,
                )
            clear_transient_storage()


def test_der02_dormant_price_sensitivity_and_replenishment_reactivation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """Dormant custody stays outside NAV across price moves until activated."""
    clear_transient_storage()
    with boa.env.anchor():
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            RETENTION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        backing_nav = alpha_token.balanceOf(stability_pool)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT
        assert stability_pool.getTotalValue(alpha_token) == backing_nav

        # Appreciation through the activation value does not auto-enumerate a
        # dormant pair; depreciation likewise leaves its raw liability intact.
        mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
        assert (
            RETENTION_THRESHOLD * 2 * EIGHTEEN_DECIMALS
            // EIGHTEEN_DECIMALS
            == ACTIVATION_THRESHOLD
        )
        assert stability_pool.getTotalValue(alpha_token) == backing_nav

        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS // 2)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_DORMANT
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == RETENTION_THRESHOLD
        assert stability_pool.getTotalValue(alpha_token) == backing_nav

        # Replenishment at the original price crosses activation and restores
        # the entire cumulative pair, including the old residual, to NAV.
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            ACTIVATION_THRESHOLD - RETENTION_THRESHOLD,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token
        ) == CLAIM_ASSET_ACTIVE
        assert stability_pool.claimableBalances(
            alpha_token, bravo_token
        ) == ACTIVATION_THRESHOLD
        assert stability_pool.getTotalValue(alpha_token) == (
            alpha_token.balanceOf(stability_pool) + ACTIVATION_THRESHOLD
        )


def test_der02_multiple_dormant_pairs_remain_non_iterable(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    delta_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """Distinct dormant pairs have custody but consume no iterable slots."""
    clear_transient_storage()
    with boa.env.anchor():
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            alice,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS,
        )
        dormant_assets = (
            (bravo_token, bravo_token_whale),
            (charlie_token, charlie_token_whale),
            (delta_token, delta_token_whale),
        )
        for claim_asset, claim_whale in dormant_assets:
            mock_price_source.setPrice(claim_asset, EIGHTEEN_DECIMALS)
            _record_claim(
                stability_pool,
                alpha_token,
                claim_asset,
                claim_whale,
                1,
                bob,
                auction_house,
                green_token,
                savings_green,
            )
            assert stability_pool.getClaimAssetState(
                alpha_token, claim_asset
            ) == CLAIM_ASSET_DORMANT
            assert stability_pool.indexOfClaimableAsset(
                alpha_token, claim_asset
            ) == 0

        assert len(dormant_assets) == 3
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
        assert stability_pool.numClaimableAssets(alpha_token) == 0
        assert stability_pool.getTotalValue(alpha_token) == alpha_token.balanceOf(
            stability_pool
        )
        _, depleted = stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            MAX_UINT256,
            bob,
            sender=teller.address,
        )
        assert depleted
        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.userBalances(alice, alpha_token) != 0
        _, depleted = stability_pool.withdrawTokensFromVault(
            alice,
            alpha_token,
            MAX_UINT256,
            alice,
            sender=teller.address,
        )
        assert depleted
        assert stability_pool.totalBalances(alpha_token) == 0
        for claim_asset, _ in dormant_assets:
            assert claim_asset.balanceOf(stability_pool) == 1
            assert stability_pool.claimableBalances(alpha_token, claim_asset) == 1
            assert stability_pool.totalClaimableBalances(claim_asset) == 1


def test_redemption_fails_closed_during_outage_and_resumes_after_restoration(
    stability_pool, alpha_token, bravo_token, bob, whale, teller, green_token,
    mock_price_source, vault_book, priced_claim_pool,
):
    """Section 8.3: redemption before, during, and after a zero-price outage."""
    vault_id = vault_book.getRegId(stability_pool)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    redeem_amount = 5 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount * 2, sender=whale)
    green_token.approve(teller, redeem_amount * 2, sender=bob)

    # During the outage the redemption fails closed and changes nothing.
    mock_price_source.setPrice(bravo_token, 0)
    with boa.reverts():
        stability_pool.getTotalValue(alpha_token)
    before = _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], include_values=False
    )
    with boa.reverts():
        redeem_from_stability_pool(
            teller, vault_id, bravo_token, redeem_amount, bob, sender=bob
        )
    assert _stab_state_snapshot(
        stability_pool, alpha_token, [bravo_token], [bob], include_values=False
    ) == before

    # After restoration it succeeds and reduces the recorded liability exactly.
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    liability_before = stability_pool.totalClaimableBalances(bravo_token)
    recipient_before = bravo_token.balanceOf(bob)

    redeem_from_stability_pool(
        teller, vault_id, bravo_token, redeem_amount, bob, sender=bob
    )

    delivered = bravo_token.balanceOf(bob) - recipient_before
    assert delivered != 0
    assert stability_pool.totalClaimableBalances(bravo_token) == liability_before - delivered
