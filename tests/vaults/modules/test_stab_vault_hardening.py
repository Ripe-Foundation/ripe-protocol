import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ACTIVATION_THRESHOLD = 25 * 10**16
CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2
DORMANT_BELOW_FLOOR = 1
DORMANT_NO_PRICE = 2
DORMANT_CAPACITY = 3
DEACTIVATION_DUST = 2


def test_deployed_runtime_fits_eip170(stability_pool):
    runtime = boa.env.get_code(stability_pool.address)
    assert len(runtime) == 24_568
    assert len(runtime) <= 24_576


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


def test_unpriced_receipt_is_accounted_dormant_without_event_spam(
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
    assert _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    ) == 1

    dormant = filter_logs(stability_pool, "ClaimAssetLeftDormant")
    assert len(dormant) == 1
    assert dormant[0].reason == DORMANT_NO_PRICE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == amount
    assert stability_pool.totalClaimableBalances(bravo_token) == amount
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token, bravo_token], sender=bob)
    assert filter_logs(stability_pool, "ClaimAssetLeftDormant") == []
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT


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
        teller.claimFromStabilityPool(
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
        (bravo_token, bravo_token_whale, 25 * 10**16),
        (charlie_token, charlie_token_whale, 250_000),
        (delta_token, delta_token_whale, 25_000_000),
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


def test_cap_prune_swap_and_pop_and_permissionless_reactivation_while_paused(
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

    tokens = []
    for index in range(13):
        token = _deploy_claim_token(governance, alice, index, ACTIVATION_THRESHOLD)
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
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
        tokens.append(token)

    dormant = filter_logs(stability_pool, "ClaimAssetLeftDormant")
    assert len(dormant) == 1
    assert dormant[0].activeCount == 12
    assert dormant[0].reason == DORMANT_CAPACITY
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 12
    assert stability_pool.numClaimableAssets(alpha_token) == 13
    assert stability_pool.getClaimAssetState(alpha_token, tokens[12]) == CLAIM_ASSET_DORMANT
    assert stability_pool.indexOfClaimableAsset(alpha_token, tokens[12]) == 0
    assert stability_pool.claimableBalances(alpha_token, tokens[12]) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(tokens[12]) == ACTIVATION_THRESHOLD

    stab_address = _asset_address(alpha_token)
    expected_pairs = {
        _claim_pair(alpha_token, token): ACTIVATION_THRESHOLD
        for token in tokens
    }
    expected_active = {stab_address: tokens[:12]}
    expected_num_assets = {stab_address: 13}
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    removed = tokens[4]
    moved = tokens[11]
    assert stability_pool.indexOfClaimableAsset(alpha_token, removed) == 5
    assert stability_pool.indexOfClaimableAsset(alpha_token, moved) == 12
    mock_price_source.setPrice(removed, 2 * 10**17)

    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [removed, removed, ZERO_ADDRESS],
        sender=alice,
    )

    deactivated = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(deactivated) == 1
    assert deactivated[0].balance == ACTIVATION_THRESHOLD
    assert deactivated[0].activeCount == 11
    assert deactivated[0].reason == DEACTIVATION_DUST
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 11
    assert stability_pool.numClaimableAssets(alpha_token) == 12
    assert stability_pool.getClaimAssetState(alpha_token, removed) == CLAIM_ASSET_DORMANT
    assert stability_pool.claimableBalances(alpha_token, removed) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(removed) == ACTIVATION_THRESHOLD
    assert stability_pool.claimableAssets(alpha_token, 5) == moved.address
    assert stability_pool.indexOfClaimableAsset(alpha_token, moved) == 5
    assert stability_pool.claimableAssets(alpha_token, 12) == ZERO_ADDRESS

    expected_active[stab_address] = (
        tokens[:4] + [tokens[11]] + tokens[5:11]
    )
    expected_num_assets[stab_address] = 12
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
        [tokens[12], tokens[12], ZERO_ADDRESS],
        sender=alice,
    )
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 12
    assert stability_pool.numClaimableAssets(alpha_token) == 13
    assert stability_pool.getClaimAssetState(alpha_token, tokens[12]) == CLAIM_ASSET_ACTIVE
    assert stability_pool.indexOfClaimableAsset(alpha_token, tokens[12]) == 12
    assert stability_pool.claimableAssets(alpha_token, 12) == tokens[12].address
    assert stability_pool.claimableBalances(alpha_token, tokens[12]) == ACTIVATION_THRESHOLD
    assert stability_pool.totalClaimableBalances(tokens[12]) == ACTIVATION_THRESHOLD

    expected_active[stab_address].append(tokens[12])
    expected_num_assets[stab_address] = 13
    _assert_claim_data_model(
        stability_pool,
        [alpha_token],
        tokens,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    seen = set()
    for index in range(1, 13):
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


def test_recovery_blocks_active_and_dormant_aggregate_liabilities_and_is_atomic(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
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
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
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
    _record_claim(
        stability_pool,
        alpha_token,
        charlie_token,
        charlie_token_whale,
        249_999,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_DORMANT

    for liable_asset in (bravo_token, charlie_token):
        with boa.reverts("claim liability exists"):
            stability_pool.recoverFunds(
                bob,
                liable_asset,
                sender=switchboard_alpha.address,
            )

    recoverable = _deploy_claim_token(governance, alice, 70, 50)
    recoverable.transfer(stability_pool, 50, sender=alice)
    with boa.reverts("no perms"):
        stability_pool.recoverFunds(bob, recoverable, sender=alice)
    assert recoverable.balanceOf(stability_pool) == 50

    with boa.reverts("claim liability exists"):
        stability_pool.recoverFundsMany(
            bob,
            [recoverable, bravo_token],
            sender=switchboard_alpha.address,
        )
    assert recoverable.balanceOf(stability_pool) == 50
    assert recoverable.balanceOf(bob) == 0

    stability_pool.recoverFunds(
        bob,
        recoverable,
        sender=switchboard_alpha.address,
    )
    recovered = filter_logs(stability_pool, "VaultFundsRecovered")
    assert len(recovered) == 1
    assert recovered[0].asset == recoverable.address
    assert recovered[0].recipient == bob
    assert recovered[0].balance == 50
    assert recoverable.balanceOf(stability_pool) == 0
    assert recoverable.balanceOf(bob) == 50


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


def test_green_repoint_cannot_bypass_stability_asset_guard(
    stability_pool,
    ripe_hq_deploy,
    governance,
    alice,
    teller,
):
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

        replacement_green.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alice)
        with boa.reverts("green cannot be stab asset"):
            stability_pool.depositTokensInVault(
                alice,
                replacement_green,
                EIGHTEEN_DECIMALS,
                sender=teller.address,
            )


def test_manual_activation_is_blocked_until_pool_is_paused(
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
        100 * EIGHTEEN_DECIMALS + 13,
    )

    active_assets = []
    for index in range(12):
        asset = _deploy_claim_token(governance, alice, index + 200, ACTIVATION_THRESHOLD)
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

    dormant = _deploy_claim_token(governance, alice, 300, 500 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(dormant, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        dormant,
        alice,
        500 * EIGHTEEN_DECIMALS,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, dormant) == CLAIM_ASSET_DORMANT

    attack_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, attack_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        alice,
        alpha_token,
        attack_deposit,
        sender=teller.address,
    )

    mock_price_source.setPrice(active_assets[0], 2 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [active_assets[0]], sender=alice)
    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(alpha_token, [dormant], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, dormant) == CLAIM_ASSET_DORMANT

    withdrawn, _ = stability_pool.withdrawTokensFromVault(
        alice,
        alpha_token,
        2**256 - 1,
        alice,
        sender=teller.address,
    )
    assert withdrawn <= attack_deposit


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
        0,
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
        mock_price_source.setPrice(token, 0)
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

    partial_claim = 2 * 10**17
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
    assert 0 < remaining < 10**17
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
    assert teller.redeemFromStabilityPool(
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
    expected_active[charlie_address] = [claim]
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )

    # The second redemption dusts the remaining claim pair while cumulative
    # GREEN reaches the activation floor in the same transaction.
    second_redemption = 15 * 10**16
    green_token.transfer(bob, second_redemption, sender=whale)
    green_token.approve(teller, second_redemption, sender=bob)
    assert teller.redeemFromStabilityPool(
        vault_id,
        claim,
        second_redemption,
        bob,
        sender=bob,
    ) == second_redemption

    expected_pairs.update(
        {
            _claim_pair(charlie_token, claim): 5 * 10**16,
            _claim_pair(charlie_token, green_token): ACTIVATION_THRESHOLD,
        }
    )
    expected_active[charlie_address] = [green_token]
    _assert_claim_data_model(
        stability_pool,
        stab_assets,
        claim_assets,
        expected_pairs,
        expected_active,
        expected_num_assets,
    )
