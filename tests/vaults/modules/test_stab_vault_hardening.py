import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


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
    assert len(runtime) == 24_575
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
