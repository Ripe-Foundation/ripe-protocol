import boa
import pytest
from hypothesis import HealthCheck, example, given, settings, strategies as st

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import ensure_token_scale, redeem_from_stability_pool
from test_stab_vault_hardening import (
    ACTIVATION_THRESHOLD,
    CLAIM_ASSET_ACTIVE,
    CLAIM_ASSET_DORMANT,
    MAX_ACTIVE_CLAIM_ASSETS,
    _assert_claim_data_model,
    _asset_address,
    _claim_pair,
    _exact_activation_price,
    _record_claim,
    _seed_stability_asset,
)


pytestmark = pytest.mark.fuzz


RETENTION_THRESHOLD = 5 * 10**16
LIVE_RESIDUAL_DIVISOR = 10**10
NUM_FUZZ_CLAIM_ASSETS = 4
PROLOGUE_TOKEN_INDEX = NUM_FUZZ_CLAIM_ASSETS
PROLOGUE_DORMANT_AMOUNT = ACTIVATION_THRESHOLD - 1
PROLOGUE_PRUNE_PRICE = 10**15


@pytest.fixture(scope="module")
def fuzz_claim_tokens(governance):
    """Reuse one 21-address token pool; anchors restore state per example."""
    factory = boa.load_partial("contracts/mock/MockErc20.vy")
    return tuple(
        factory.deploy(
            governance,
            f"Fuzz Claim {index}",
            f"FC{index}",
            18,
            0,
        )
        for index in range(MAX_ACTIVE_CLAIM_ASSETS + 1)
    )


def _prepare_claim_token(
    token,
    governance,
    holder,
    amount,
    price_desk=None,
    switchboard_bravo=None,
):
    token.mint(holder, amount, sender=governance.address)
    if price_desk is not None:
        sender = (
            switchboard_bravo.address
            if switchboard_bravo is not None
            else governance.address
        )
        ensure_token_scale(price_desk, token, sender)
    return token


CLAIM_AMOUNT_STRATEGY = st.one_of(
    st.sampled_from(
        [
            1,
            RETENTION_THRESHOLD - 1,
            RETENTION_THRESHOLD,
            RETENTION_THRESHOLD + 1,
            ACTIVATION_THRESHOLD - 1,
            ACTIVATION_THRESHOLD,
            ACTIVATION_THRESHOLD + 1,
            3 * 10**17,
        ]
    ),
    st.integers(min_value=1, max_value=3 * 10**17),
)
PRICE_STRATEGY = st.sampled_from(
    [
        2 * 10**17,
        EIGHTEEN_DECIMALS // 2,
        EIGHTEEN_DECIMALS,
        2 * EIGHTEEN_DECIMALS,
    ]
)
LIFECYCLE_OPERATION_STRATEGY = st.lists(
    st.tuples(
        st.sampled_from(["add", "prune", "activate", "deposit", "withdraw"]),
        st.integers(min_value=0, max_value=NUM_FUZZ_CLAIM_ASSETS - 1),
        CLAIM_AMOUNT_STRATEGY,
        PRICE_STRATEGY,
    ),
    min_size=1,
    max_size=16,
)
CAPACITY_CASE_STRATEGY = st.tuples(
    st.integers(
        min_value=ACTIVATION_THRESHOLD,
        max_value=3 * EIGHTEEN_DECIMALS,
    ),
    st.integers(min_value=1, max_value=3 * 10**17),
)


@st.composite
def claim_reduction_cases(draw):
    pair_balance = draw(
        st.one_of(
            st.sampled_from(
                [
                    ACTIVATION_THRESHOLD,
                    ACTIVATION_THRESHOLD + 1,
                    5 * 10**17,
                    EIGHTEEN_DECIMALS,
                ]
            ),
            st.integers(
                min_value=ACTIVATION_THRESHOLD,
                max_value=2 * EIGHTEEN_DECIMALS,
            ),
        )
    )
    bound = pair_balance // LIVE_RESIDUAL_DIVISOR
    consume_at_bound = pair_balance - bound
    consume_above_bound = pair_balance - bound - 1
    sampled_claims = [
        10**15,
        RETENTION_THRESHOLD - 1,
        RETENTION_THRESHOLD,
        ACTIVATION_THRESHOLD,
        pair_balance,
        consume_at_bound,
    ]
    if consume_above_bound >= 1:
        sampled_claims.append(consume_above_bound)
    max_claim_value = draw(
        st.one_of(
            st.sampled_from(sampled_claims).filter(lambda value: 1 <= value <= pair_balance),
            st.integers(min_value=10**15, max_value=pair_balance),
        )
    )
    return pair_balance, max_claim_value


@st.composite
def redemption_cases(draw):
    alpha_balance = draw(
        st.integers(
            min_value=ACTIVATION_THRESHOLD,
            max_value=EIGHTEEN_DECIMALS,
        )
    )
    charlie_balance = draw(
        st.integers(
            min_value=ACTIVATION_THRESHOLD,
            max_value=EIGHTEEN_DECIMALS,
        )
    )
    total_payment = draw(
        st.integers(
            min_value=1,
            max_value=alpha_balance + charlie_balance,
        )
    )
    first_payment = draw(st.integers(min_value=1, max_value=total_payment))
    return (
        alpha_balance,
        charlie_balance,
        first_payment,
        total_payment - first_payment,
    )


def _swap_pop(active_assets, asset):
    index = active_assets.index(asset)
    active_assets[index] = active_assets[-1]
    active_assets.pop()


def _production_remaining_usd(remaining_balance, claimed_amount, claimed_usd):
    """Mirror StabVault remainingUsdValue, including the precision-loss floor to 1."""
    if remaining_balance == 0 or claimed_amount == 0:
        return 0
    numerator = remaining_balance * claimed_usd
    if numerator < claimed_amount:
        return 1
    return numerator // claimed_amount


def _should_unlist_residual(prev_pair, remaining_balance, remaining_usd, total_balances):
    if remaining_balance == 0:
        return True
    if remaining_usd == 0 or remaining_usd >= RETENTION_THRESHOLD:
        return False
    return (
        total_balances == 0
        or remaining_balance <= prev_pair // LIVE_RESIDUAL_DIVISOR
    )


def _production_redeem_remaining_usd(remaining_balance, max_redeem_value, max_claimable_amount):
    """Mirror `_redeemFromStabilityPool` remainingUsdValue at this call's ratio."""
    if remaining_balance == 0 or max_claimable_amount == 0:
        return 0
    numerator = remaining_balance * max_redeem_value
    if numerator < max_claimable_amount:
        return 1
    return numerator // max_claimable_amount


@settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(operations=LIFECYCLE_OPERATION_STRATEGY)
def test_fuzz_claim_data_add_prune_activate_sequences(
    operations,
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
    fuzz_claim_tokens,
    price_desk,
    switchboard_bravo,
):
    with boa.env.anchor():
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
        )
        sampled_tokens = [
            _prepare_claim_token(
                fuzz_claim_tokens[index],
                governance,
                alice,
                20 * EIGHTEEN_DECIMALS,
                price_desk,
                switchboard_bravo,
            )
            for index in range(NUM_FUZZ_CLAIM_ASSETS)
        ]
        prologue_token = _prepare_claim_token(
            fuzz_claim_tokens[PROLOGUE_TOKEN_INDEX],
            governance,
            alice,
            20 * EIGHTEEN_DECIMALS,
            price_desk,
            switchboard_bravo,
        )
        tokens = sampled_tokens + [prologue_token]

        stab_address = _asset_address(alpha_token)
        expected_pairs = {}
        active_assets = []
        expected_num_assets = 0
        is_paused = False
        prologue_seated = False
        prologue_delisted = False

        mock_price_source.setPrice(prologue_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            prologue_token,
            alice,
            PROLOGUE_DORMANT_AMOUNT,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, prologue_token,
        ) == CLAIM_ASSET_DORMANT
        expected_pairs[_claim_pair(alpha_token, prologue_token)] = (
            PROLOGUE_DORMANT_AMOUNT
        )

        withdrawn, _ = stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            MAX_UINT256,
            bob,
            sender=teller.address,
        )
        assert withdrawn != 0
        assert stability_pool.totalBalances(alpha_token) == 0

        mock_price_source.setPrice(
            prologue_token,
            _exact_activation_price(PROLOGUE_DORMANT_AMOUNT),
        )
        count_before_seat = stability_pool.getNumActiveClaimAssets(alpha_token)
        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(
            alpha_token, [prologue_token], sender=alice,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, prologue_token,
        ) == CLAIM_ASSET_ACTIVE
        count_after_seat = stability_pool.getNumActiveClaimAssets(alpha_token)
        assert count_after_seat == count_before_seat + 1
        prologue_seated = True
        stability_pool.pause(False, sender=switchboard_alpha.address)

        mock_price_source.setPrice(prologue_token, PROLOGUE_PRUNE_PRICE)
        count_before_delist = stability_pool.getNumActiveClaimAssets(alpha_token)
        stability_pool.pruneClaimableAssets(
            alpha_token, [prologue_token], sender=alice,
        )
        assert stability_pool.getClaimAssetState(
            alpha_token, prologue_token,
        ) == CLAIM_ASSET_DORMANT
        count_after_delist = stability_pool.getNumActiveClaimAssets(alpha_token)
        assert count_after_delist == count_before_delist - 1
        prologue_delisted = True
        expected_num_assets = 1

        _assert_claim_data_model(
            stability_pool,
            [alpha_token],
            tokens,
            expected_pairs,
            {stab_address: list(active_assets)},
            {stab_address: expected_num_assets},
        )

        for operation, token_index, amount, price in operations:
            token = sampled_tokens[token_index]
            token_address = _asset_address(token)
            pair_key = _claim_pair(alpha_token, token)
            mock_price_source.setPrice(token, price)

            if operation == "add":
                if is_paused:
                    stability_pool.pause(
                        False,
                        sender=switchboard_alpha.address,
                    )
                    is_paused = False

                if (
                    stability_pool.totalBalances(alpha_token) == 0
                    and alpha_token.balanceOf(stability_pool)
                    <= stability_pool.totalClaimableBalances(alpha_token)
                ):
                    alpha_token.transfer(
                        stability_pool,
                        EIGHTEEN_DECIMALS,
                        sender=alpha_token_whale,
                    )

                active_addresses = [_asset_address(asset) for asset in active_assets]
                is_active = token_address in active_addresses
                if not is_active and price == 0:
                    with boa.env.anchor():
                        with boa.reverts("no price for claim asset"):
                            _record_claim(
                                stability_pool,
                                alpha_token,
                                token,
                                alice,
                                amount,
                                bob,
                                auction_house,
                                green_token,
                                savings_green,
                            )
                else:
                    _record_claim(
                        stability_pool,
                        alpha_token,
                        token,
                        alice,
                        amount,
                        bob,
                        auction_house,
                        green_token,
                        savings_green,
                    )
                    expected_pairs[pair_key] = expected_pairs.get(pair_key, 0) + amount
                    usd_value = expected_pairs[pair_key] * price // EIGHTEEN_DECIMALS
                    if not is_active and usd_value >= ACTIVATION_THRESHOLD:
                        active_assets.append(token)
                        expected_num_assets = len(active_assets) + 1

            elif operation == "prune":
                stability_pool.pruneClaimableAssets(
                    alpha_token,
                    [token, token, ZERO_ADDRESS],
                    sender=alice,
                )
                active_addresses = [_asset_address(asset) for asset in active_assets]
                pair_balance = expected_pairs.get(pair_key, 0)
                usd_value = pair_balance * price // EIGHTEEN_DECIMALS
                if (
                    stability_pool.totalBalances(alpha_token) == 0
                    and token_address in active_addresses
                    and usd_value != 0
                    and usd_value < RETENTION_THRESHOLD
                ):
                    _swap_pop(active_assets, token)
                    expected_num_assets = len(active_assets) + 1

            elif operation == "activate":
                if not is_paused:
                    stability_pool.pause(
                        True,
                        sender=switchboard_alpha.address,
                    )
                    is_paused = True

                stability_pool.activateClaimAssets(
                    alpha_token,
                    [token, token, ZERO_ADDRESS],
                    sender=alice,
                )
                active_addresses = [_asset_address(asset) for asset in active_assets]
                pair_balance = expected_pairs.get(pair_key, 0)
                usd_value = pair_balance * price // EIGHTEEN_DECIMALS
                if (
                    stability_pool.totalBalances(alpha_token) == 0
                    and pair_balance != 0
                    and token_address not in active_addresses
                    and usd_value >= ACTIVATION_THRESHOLD
                ):
                    active_assets.append(token)
                    expected_num_assets = len(active_assets) + 1

            elif operation == "deposit":
                if is_paused:
                    stability_pool.pause(
                        False,
                        sender=switchboard_alpha.address,
                    )
                    is_paused = False

                # Capacity and bounded dormant dust do not freeze deposits.
                deposit_amount = max(amount, 10**15)
                with boa.env.anchor():
                    alpha_token.transfer(
                        stability_pool,
                        deposit_amount,
                        sender=alpha_token_whale,
                    )
                    assert stability_pool.depositTokensInVault(
                        alice,
                        alpha_token,
                        deposit_amount,
                        sender=teller.address,
                    ) == deposit_amount

            else:
                if is_paused:
                    stability_pool.pause(
                        False,
                        sender=switchboard_alpha.address,
                    )
                    is_paused = False

                # Persist a real full exit so later prune/activate see an empty
                # cohort. Replenish unreserved stab custody before a later
                # liquidation receipt, or that receipt reverts `nothing to transfer`.
                if stability_pool.userBalances(bob, alpha_token) != 0:
                    withdrawn, _ = stability_pool.withdrawTokensFromVault(
                        bob,
                        alpha_token,
                        MAX_UINT256,
                        bob,
                        sender=teller.address,
                    )
                    assert withdrawn != 0

            _assert_claim_data_model(
                stability_pool,
                [alpha_token],
                tokens,
                expected_pairs,
                {stab_address: list(active_assets)},
                {stab_address: expected_num_assets},
            )

        assert prologue_seated and prologue_delisted
        assert stability_pool.getClaimAssetState(
            alpha_token, prologue_token,
        ) == CLAIM_ASSET_DORMANT
        assert expected_pairs[_claim_pair(alpha_token, prologue_token)] == (
            PROLOGUE_DORMANT_AMOUNT
        )


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(case=CAPACITY_CASE_STRATEGY)
def test_fuzz_capacity_rejection_existing_receipt_and_readdition(
    case,
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
    fuzz_claim_tokens,
    price_desk,
    switchboard_bravo,
):
    candidate_amount, active_increment = case

    with boa.env.anchor():
        setGeneralConfig()
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
            100 * EIGHTEEN_DECIMALS + 14,
        )
        active_tokens = [
            _prepare_claim_token(
                fuzz_claim_tokens[index],
                governance,
                alice,
                ACTIVATION_THRESHOLD + (active_increment if index == 0 else 0),
                price_desk,
                switchboard_bravo,
            )
            for index in range(MAX_ACTIVE_CLAIM_ASSETS)
        ]
        for token in active_tokens:
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

        candidate = _prepare_claim_token(
            fuzz_claim_tokens[MAX_ACTIVE_CLAIM_ASSETS],
            governance,
            alice,
            candidate_amount,
            price_desk,
            switchboard_bravo,
        )
        mock_price_source.setPrice(candidate, EIGHTEEN_DECIMALS)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
            MAX_ACTIVE_CLAIM_ASSETS
        )
        assert stability_pool.canAcceptLiquidationAsset(alpha_token, active_tokens[0])
        assert not stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)

        with boa.env.anchor():
            with boa.reverts("max active claim assets"):
                _record_claim(
                    stability_pool,
                    alpha_token,
                    candidate,
                    alice,
                    candidate_amount,
                    bob,
                    auction_house,
                    green_token,
                    savings_green,
                )
            assert stability_pool.claimableBalances(alpha_token, candidate) == 0
            assert stability_pool.totalClaimableBalances(candidate) == 0

        assert stability_pool.indexOfClaimableAsset(alpha_token, candidate) == 0
        assert stability_pool.claimableBalances(alpha_token, candidate) == 0

        # A full active set does not freeze deposits.
        with boa.env.anchor():
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

        # Existing active claim assets remain consumable at the cap.
        _record_claim(
            stability_pool,
            alpha_token,
            active_tokens[0],
            alice,
            active_increment,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.claimableBalances(
            alpha_token,
            active_tokens[0],
        ) == ACTIVATION_THRESHOLD + active_increment
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
            MAX_ACTIVE_CLAIM_ASSETS
        )

        # Claim an occupant to zero to free one slot for the candidate.
        setAssetConfig(active_tokens[1])
        stability_pool.claimManyFromStabilityPool(
            bob,
            [(alpha_token.address, active_tokens[1].address, MAX_UINT256)],
            bob,
            False,
            sender=teller.address,
        )
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
            MAX_ACTIVE_CLAIM_ASSETS - 1
        )
        assert stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)

        _record_claim(
            stability_pool,
            alpha_token,
            candidate,
            alice,
            candidate_amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == (
            MAX_ACTIVE_CLAIM_ASSETS
        )
        assert stability_pool.indexOfClaimableAsset(alpha_token, candidate) != 0
        assert stability_pool.claimableBalances(alpha_token, candidate) == (
            candidate_amount
        )

        with boa.env.anchor():
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


@settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(case=claim_reduction_cases())
@example(case=(
    EIGHTEEN_DECIMALS,
    EIGHTEEN_DECIMALS - EIGHTEEN_DECIMALS // LIVE_RESIDUAL_DIVISOR,
))
@example(case=(
    EIGHTEEN_DECIMALS,
    EIGHTEEN_DECIMALS - EIGHTEEN_DECIMALS // LIVE_RESIDUAL_DIVISOR - 1,
))
def test_fuzz_claim_data_reductions_preserve_shared_liability_model(
    case,
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
    fuzz_claim_tokens,
    price_desk,
    switchboard_bravo,
):
    pair_balance, max_claim_value = case

    with boa.env.anchor():
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

        claim = _prepare_claim_token(
            fuzz_claim_tokens[0],
            governance,
            alice,
            2 * pair_balance,
            price_desk,
            switchboard_bravo,
        )
        setAssetConfig(claim)
        mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)
        for stab_asset in (alpha_token, charlie_token):
            _record_claim(
                stability_pool,
                stab_asset,
                claim,
                alice,
                pair_balance,
                bob,
                auction_house,
                green_token,
                savings_green,
            )

        stab_assets = [alpha_token, charlie_token]
        alpha_address = _asset_address(alpha_token)
        charlie_address = _asset_address(charlie_token)
        expected_pairs = {
            _claim_pair(alpha_token, claim): pair_balance,
            _claim_pair(charlie_token, claim): pair_balance,
        }
        expected_active = {
            alpha_address: [claim],
            charlie_address: [claim],
        }
        expected_num_assets = {
            alpha_address: 2,
            charlie_address: 2,
        }

        balance_before = claim.balanceOf(bob)
        claim_usd_value = stability_pool.claimManyFromStabilityPool(
            bob,
            [(alpha_token.address, claim.address, max_claim_value)],
            bob,
            False,
            sender=teller.address,
        )
        claimed_amount = claim.balanceOf(bob) - balance_before
        assert claim_usd_value != 0
        assert 0 < claimed_amount <= pair_balance

        remaining_balance = pair_balance - claimed_amount
        remaining_usd_value = _production_remaining_usd(
            remaining_balance, claimed_amount, claim_usd_value,
        )

        should_remove = _should_unlist_residual(
            pair_balance,
            remaining_balance,
            remaining_usd_value,
            stability_pool.totalBalances(alpha_token),
        )
        expected_pairs[_claim_pair(alpha_token, claim)] = remaining_balance
        if should_remove:
            expected_active[alpha_address] = []
            expected_num_assets[alpha_address] = 1

        _assert_claim_data_model(
            stability_pool,
            stab_assets,
            [claim],
            expected_pairs,
            expected_active,
            expected_num_assets,
        )

        if remaining_balance != 0:
            balance_before = claim.balanceOf(bob)
            stability_pool.claimManyFromStabilityPool(
                bob,
                [(alpha_token.address, claim.address, MAX_UINT256)],
                bob,
                False,
                sender=teller.address,
            )
            assert claim.balanceOf(bob) - balance_before == remaining_balance
            expected_pairs[_claim_pair(alpha_token, claim)] = 0
            expected_active[alpha_address] = []
            expected_num_assets[alpha_address] = 1
            _assert_claim_data_model(
                stability_pool,
                stab_assets,
                [claim],
                expected_pairs,
                expected_active,
                expected_num_assets,
            )


@settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(case=redemption_cases())
@example(case=(
    EIGHTEEN_DECIMALS,
    ACTIVATION_THRESHOLD,
    EIGHTEEN_DECIMALS - EIGHTEEN_DECIMALS // LIVE_RESIDUAL_DIVISOR,
    0,
))
@example(case=(
    EIGHTEEN_DECIMALS,
    ACTIVATION_THRESHOLD,
    EIGHTEEN_DECIMALS - EIGHTEEN_DECIMALS // LIVE_RESIDUAL_DIVISOR - 1,
    0,
))
def test_fuzz_redemptions_preserve_claim_and_green_registry_model(
    case,
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
    fuzz_claim_tokens,
    price_desk,
    switchboard_bravo,
):
    alpha_balance, charlie_balance, first_payment, second_payment = case

    with boa.env.anchor():
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

        claim = _prepare_claim_token(
            fuzz_claim_tokens[0],
            governance,
            alice,
            alpha_balance + charlie_balance,
            price_desk,
            switchboard_bravo,
        )
        setAssetConfig(claim)
        mock_price_source.setPrice(claim, EIGHTEEN_DECIMALS)
        for stab_asset, balance in (
            (alpha_token, alpha_balance),
            (charlie_token, charlie_balance),
        ):
            _record_claim(
                stability_pool,
                stab_asset,
                claim,
                alice,
                balance,
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
            _claim_pair(alpha_token, claim): alpha_balance,
            _claim_pair(charlie_token, claim): charlie_balance,
        }
        expected_active = {
            alpha_address: [claim],
            charlie_address: [claim],
        }
        expected_num_assets = {
            alpha_address: 2,
            charlie_address: 2,
        }
        remaining_claims = {
            alpha_address: alpha_balance,
            charlie_address: charlie_balance,
        }
        green_pairs = {
            alpha_address: 0,
            charlie_address: 0,
        }
        asset_by_address = {
            alpha_address: alpha_token,
            charlie_address: charlie_token,
        }

        vault_id = vault_book.getRegId(stability_pool)
        for payment in (first_payment, second_payment):
            if payment == 0:
                continue

            green_token.transfer(bob, payment, sender=whale)
            green_token.approve(teller, payment, sender=bob)
            assert (
                redeem_from_stability_pool(teller,
                    vault_id,
                    claim,
                    payment,
                    bob,
                    sender=bob,
                )
                == payment
            )

            payment_remaining = payment
            for stab_address in (alpha_address, charlie_address):
                if payment_remaining == 0:
                    break

                stab_asset = asset_by_address[stab_address]
                prev_pair = remaining_claims[stab_address]
                claim_amount = min(payment_remaining, prev_pair)
                if claim_amount == 0:
                    continue

                remaining_claims[stab_address] = prev_pair - claim_amount
                expected_pairs[_claim_pair(stab_asset, claim)] = remaining_claims[
                    stab_address
                ]
                remaining_usd_value = _production_redeem_remaining_usd(
                    remaining_claims[stab_address],
                    payment,
                    payment,
                )
                if _should_unlist_residual(
                    prev_pair,
                    remaining_claims[stab_address],
                    remaining_usd_value,
                    stability_pool.totalBalances(stab_asset),
                ):
                    active_addresses = [
                        _asset_address(asset) for asset in expected_active[stab_address]
                    ]
                    if _asset_address(claim) in active_addresses:
                        _swap_pop(expected_active[stab_address], claim)

                green_pairs[stab_address] += claim_amount
                expected_pairs[_claim_pair(stab_asset, green_token)] = green_pairs[
                    stab_address
                ]
                active_addresses = [
                    _asset_address(asset) for asset in expected_active[stab_address]
                ]
                if (
                    _asset_address(green_token) not in active_addresses
                    and green_pairs[stab_address] >= ACTIVATION_THRESHOLD
                ):
                    expected_active[stab_address].append(green_token)

                expected_num_assets[stab_address] = (
                    len(expected_active[stab_address]) + 1
                )
                payment_remaining -= claim_amount

            assert payment_remaining == 0
            _assert_claim_data_model(
                stability_pool,
                stab_assets,
                claim_assets,
                expected_pairs,
                expected_active,
                expected_num_assets,
            )
