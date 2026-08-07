import boa
from eth_abi import encode
from eth_utils import keccak

from conf_utils import claim_from_stability_pool, filter_logs, redeem_from_stability_pool
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
DEACTIVATION_NO_PRICE = 3
CLAIM_ASSET_NO_PRICE_QUARANTINED = 3
MAX_ACTIVE_CLAIM_ASSETS = 20
MAX_CLAIM_ASSET_MAINTENANCE = 15


def test_deployed_runtime_fits_eip170(stability_pool):
    runtime = boa.env.get_code(stability_pool.address)
    assert len(runtime) == 24_575
    assert 24_576 - len(runtime) == 1


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
    assert deposit_gas[-1] < 500_000
    assert withdrawal_gas[-1] < 450_000

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

    with boa.env.anchor():
        for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]:
            mock_price_source.setPrice(token, 2 * 10**17)
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

        stability_pool.pause(True, sender=switchboard_alpha.address)
        for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]:
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
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

    setGeneralConfig()
    for token in claim_tokens[:MAX_CLAIM_ASSET_MAINTENANCE]:
        setAssetConfig(token)

    with boa.env.anchor():
        gas_before = boa.env.get_gas_used()
        assert stability_pool.claimFromStabilityPool(
            bob,
            alpha_token,
            claim_tokens[0],
            10**15,
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

    # Local-EVM regression ceilings for the other public bounded paths. They
    # are not production gas estimates or assertions about a chain gas limit.
    assert existing_receipt_gas < 50_000
    assert prune_gas < 500_000
    assert activation_gas < 1_200_000
    assert single_claim_gas < 500_000
    assert claim_many_gas < 7_000_000


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


def test_no_price_quarantine_blocks_unpause_until_every_exact_pair_recovers(
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
    switchboard_bravo,
    switchboard_charlie,
    switchboard_delta,
    switchboard_echo,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    claim_assets = (
        (bravo_token, bravo_token_whale, ACTIVATION_THRESHOLD),
        (charlie_token, charlie_token_whale, 10**5),
    )
    for claim_asset, whale, amount in claim_assets:
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

    shares_before = stability_pool.userBalances(bob, alpha_token)
    custody_before = {
        token.address: token.balanceOf(stability_pool)
        for token, _, _ in claim_assets
    }
    pair_before = {
        token.address: stability_pool.claimableBalances(alpha_token, token)
        for token, _, _ in claim_assets
    }
    total_before = {
        token.address: stability_pool.totalClaimableBalances(token)
        for token, _, _ in claim_assets
    }

    # Keep the configured feed present while making its reported price zero so
    # the strict pre-pause valuation path must reject the stale value.
    mock_price_source.setPrice(bravo_token, 0)
    with boa.reverts():
        stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            1,
            bob,
            sender=teller.address,
        )

    stability_pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(charlie_token, 0)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [bravo_token, charlie_token, bravo_token],
        sender=alice,
    )

    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 2
    assert all(log.reason == DEACTIVATION_NO_PRICE for log in logs)
    assert stability_pool.noPriceQuarantineCount() == 2
    for claim_asset, _, _ in claim_assets:
        assert stability_pool.getClaimAssetState(
            alpha_token,
            claim_asset,
        ) == CLAIM_ASSET_NO_PRICE_QUARANTINED
        assert stability_pool.indexOfClaimableAsset(alpha_token, claim_asset) == 0
        assert stability_pool.claimableBalances(alpha_token, claim_asset) == pair_before[
            claim_asset.address
        ]
        assert stability_pool.totalClaimableBalances(claim_asset) == total_before[
            claim_asset.address
        ]
        assert claim_asset.balanceOf(stability_pool) == custody_before[
            claim_asset.address
        ]
    assert stability_pool.userBalances(bob, alpha_token) == shares_before

    with boa.reverts("contract paused"):
        stability_pool.depositTokensInVault(
            bob,
            alpha_token,
            1,
            sender=teller.address,
        )

    # Zero-price activation is a no-op and cannot clear either obligation.
    stability_pool.activateClaimAssets(
        alpha_token,
        [bravo_token, charlie_token],
        sender=alice,
    )
    assert stability_pool.noPriceQuarantineCount() == 2

    for switchboard in (
        switchboard_alpha,
        switchboard_bravo,
        switchboard_charlie,
        switchboard_delta,
        switchboard_echo,
    ):
        with boa.reverts("unresolved no-price quarantine"):
            stability_pool.pause(False, sender=switchboard.address)

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(
        alpha_token,
        charlie_token,
    ) == CLAIM_ASSET_NO_PRICE_QUARANTINED
    assert stability_pool.noPriceQuarantineCount() == 1
    with boa.reverts("unresolved no-price quarantine"):
        stability_pool.pause(False, sender=switchboard_alpha.address)

    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [charlie_token], sender=alice)
    assert stability_pool.noPriceQuarantineCount() == 0
    assert stability_pool.getClaimAssetState(
        alpha_token,
        charlie_token,
    ) == CLAIM_ASSET_ACTIVE
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert not stability_pool.isPaused()


def test_unpaused_prune_skips_unpriced_pair_and_continues_batch(
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
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    for claim_asset, whale, amount in (
        (bravo_token, bravo_token_whale, ACTIVATION_THRESHOLD),
        (charlie_token, charlie_token_whale, 100_000),
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

    bravo_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    charlie_balance = stability_pool.claimableBalances(alpha_token, charlie_token)
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
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == bravo_balance
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == charlie_balance
    assert stability_pool.noPriceQuarantineCount() == 0


def test_quarantine_recovery_reserves_released_capacity_until_unpause_is_safe(
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

    ordinary = _deploy_claim_token(
        governance,
        alice,
        1_600,
        ACTIVATION_THRESHOLD,
    )
    mock_price_source.setPrice(ordinary, 5 * 10**17)
    _record_claim(
        stability_pool,
        alpha_token,
        ordinary,
        alice,
        ACTIVATION_THRESHOLD,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, ordinary) == CLAIM_ASSET_DORMANT

    active = []
    for index in range(MAX_ACTIVE_CLAIM_ASSETS):
        token = _deploy_claim_token(
            governance,
            alice,
            1_601 + index,
            ACTIVATION_THRESHOLD,
        )
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
        active.append(token)

    quarantined = active[0]
    mock_price_source.setPrice(ordinary, EIGHTEEN_DECIMALS)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(quarantined, 0)
    stability_pool.pruneClaimableAssets(alpha_token, [quarantined], sender=alice)

    assert stability_pool.noPriceQuarantineCount() == 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS - 1
    assert stability_pool.getClaimAssetState(
        alpha_token,
        quarantined,
    ) == CLAIM_ASSET_NO_PRICE_QUARANTINED
    with boa.reverts("reserved"):
        stability_pool.activateClaimAssets(alpha_token, [ordinary], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, ordinary) == CLAIM_ASSET_DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS - 1
    assert stability_pool.noPriceQuarantineCount() == 1

    mock_price_source.setPrice(quarantined, EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [quarantined], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, quarantined) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, ordinary) == CLAIM_ASSET_DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS
    assert stability_pool.noPriceQuarantineCount() == 0
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert not stability_pool.isPaused()


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
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        ACTIVATION_THRESHOLD - 1,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_DORMANT

    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        1,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE

    # Exact $0.05 remains active; immediately below it prunes. The band from
    # $0.05 through $0.099... therefore preserves the existing state.
    retention_price = RETENTION_THRESHOLD * EIGHTEEN_DECIMALS // ACTIVATION_THRESHOLD
    mock_price_source.setPrice(bravo_token, retention_price)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(bravo_token, retention_price - 1)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token,
        bravo_token,
    ) == CLAIM_ASSET_DORMANT

    stability_pool.pause(True, sender=switchboard_alpha.address)
    activation_price = EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, activation_price - 1)
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
):
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
    mock_price_source.setPrice(removed, 2 * 10**17)

    stability_pool.pruneClaimableAssets(
        alpha_token,
        [removed, removed, ZERO_ADDRESS],
        sender=alice,
    )

    deactivated = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(deactivated) == 1
    assert deactivated[0].balance == ACTIVATION_THRESHOLD
    assert deactivated[0].activeCount == MAX_ACTIVE_CLAIM_ASSETS - 1
    assert deactivated[0].reason == DEACTIVATION_DUST
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
        MAX_ACTIVE_CLAIM_ASSETS - 1
    )
    assert stability_pool.numClaimableAssets(alpha_token) == MAX_ACTIVE_CLAIM_ASSETS
    assert stability_pool.getClaimAssetState(alpha_token, removed) == CLAIM_ASSET_DORMANT
    assert stability_pool.claimableBalances(alpha_token, removed) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(removed) == ACTIVATION_THRESHOLD
    assert stability_pool.claimableAssets(alpha_token, 5) == moved.address
    assert stability_pool.indexOfClaimableAsset(alpha_token, moved) == 5
    assert stability_pool.claimableAssets(
        alpha_token,
        MAX_ACTIVE_CLAIM_ASSETS,
    ) == ZERO_ADDRESS

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

    # Remove the middle entry while unpaused. The last active entry must move
    # into its slot, and duplicate/inactive candidates must be idempotent.
    mock_price_source.setPrice(tokens[1], 2 * 10**17)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [tokens[1], tokens[1], tokens[4], ZERO_ADDRESS],
        sender=alice,
    )
    expected_active[stab_address] = [tokens[0], tokens[2]]
    expected_num_assets[stab_address] = 3
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # Both dormant balances become eligible, but manual activation must not
    # mutate anything until the pool is paused.
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
    expected_active[stab_address] = [
        tokens[0],
        tokens[2],
        tokens[3],
        tokens[4],
    ]
    expected_num_assets[stab_address] = 5
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # An all-idempotent batch cannot disturb indexes or counts.
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

    # Remove the first entry, then the entry that becomes the last slot. This
    # exercises both swap-and-pop branches in one batch.
    mock_price_source.setPrice(tokens[0], 2 * 10**17)
    mock_price_source.setPrice(tokens[3], 2 * 10**17)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [tokens[0], tokens[3]],
        sender=alice,
    )
    expected_active[stab_address] = [tokens[4], tokens[2]]
    expected_num_assets[stab_address] = 3
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # Reactivation appends in candidate order and never changes balances or
    # aggregate liabilities.
    mock_price_source.setPrice(tokens[0], EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(tokens[3], EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(
        alpha_token,
        [tokens[3], tokens[0]],
        sender=alice,
    )
    expected_active[stab_address] = [
        tokens[4],
        tokens[2],
        tokens[3],
        tokens[0],
    ]
    expected_num_assets[stab_address] = 5
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
    claimed_usd_value = stability_pool.claimFromStabilityPool(
        bob,
        alpha_token,
        claim,
        partial_claim,
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
    expected_active[alpha_address] = []
    expected_num_assets[alpha_address] = 1
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
        stability_pool.claimFromStabilityPool(
            bob,
            stab_asset,
            claim,
            MAX_UINT256,
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
    expected_active[charlie_address] = [green_token]
    expected_num_assets[charlie_address] = 2
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )
