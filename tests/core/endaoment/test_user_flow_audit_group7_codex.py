import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


ONE_GREEN = EIGHTEEN_DECIMALS
ONE_USDC = 10**6
HUNDRED_PERCENT = 10_000
MAX_SAFE_INTERVAL_MINT = MAX_UINT256 // (ONE_USDC * HUNDRED_PERCENT)


def _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, payment_token, price=ONE_GREEN):
    mock_price_source.setPrice(payment_token.address, price)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)


def _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, payment_token, price=ONE_GREEN):
    mock_price_source.setPrice(payment_token.address, price)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


@pytest.mark.parametrize(
    "fee_bps,price",
    [
        (fee_bps, price)
        for fee_bps in (0, 1, 500, 9_999)
        for price in (95 * ONE_GREEN // 100, ONE_GREEN, 105 * ONE_GREEN // 100)
    ],
)
def test_g7_regular_mint_conserves_payment_supply_interval_and_event(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    fee_bps,
    price,
):
    payer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    requested = 123_456_789

    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)
    if fee_bps:
        endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)

    charlie_token.mint(payer, requested, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, requested, sender=payer)

    payer_before = charlie_token.balanceOf(payer)
    idle_before = charlie_token.balanceOf(endaoment_psm.address)
    supply_before = green_token.totalSupply()
    recipient_before = green_token.balanceOf(recipient)

    fee = requested * fee_bps // HUNDRED_PERCENT
    after_fee = requested - fee
    usd_value = price * after_fee // ONE_USDC
    one_to_one = after_fee * ONE_GREEN // ONE_USDC
    expected_green = min(usd_value, one_to_one)

    returned = endaoment_psm.mintGreen(requested, recipient, False, sender=payer)
    event = filter_logs(endaoment_psm, "MintGreen")[-1]

    assert returned == expected_green
    assert payer_before - charlie_token.balanceOf(payer) == requested
    assert charlie_token.balanceOf(endaoment_psm.address) - idle_before == requested
    assert green_token.totalSupply() - supply_before == expected_green
    assert green_token.balanceOf(recipient) - recipient_before == expected_green
    assert endaoment_psm.globalMintInterval().amount == expected_green
    assert event.user == recipient
    assert event.sender == payer
    assert event.usdcIn == requested
    assert event.greenOut == expected_green
    assert event.usdcFee == fee
    assert not event.receivedSavingsGreen


def test_g7_mint_to_psm_keeps_usdc_payment_external_and_green_as_residue(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    payer = boa.env.generate_address()
    payment = 37 * ONE_USDC
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(payer, payment, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, payment, sender=payer)

    returned = endaoment_psm.mintGreen(payment, endaoment_psm.address, False, sender=payer)

    assert charlie_token.balanceOf(payer) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == payment
    assert green_token.balanceOf(endaoment_psm.address) == returned == 37 * ONE_GREEN


def test_g7_regular_hundred_percent_mint_fee_reverts_before_payment_pull(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    payer = boa.env.generate_address()
    payment = 10 * ONE_USDC
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)
    charlie_token.mint(payer, payment, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, payment, sender=payer)

    before = (
        charlie_token.balanceOf(payer),
        charlie_token.balanceOf(endaoment_psm.address),
        charlie_token.allowance(payer, endaoment_psm.address),
        green_token.totalSupply(),
        endaoment_psm.globalMintInterval(),
        len(filter_logs(endaoment_psm, "MintGreen")),
    )
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(payment, payer, False, sender=payer)

    assert charlie_token.balanceOf(payer) == before[0]
    assert charlie_token.balanceOf(endaoment_psm.address) == before[1]
    assert charlie_token.allowance(payer, endaoment_psm.address) == before[2]
    assert green_token.totalSupply() == before[3]
    assert endaoment_psm.globalMintInterval() == before[4]
    assert len(filter_logs(endaoment_psm, "MintGreen")) == before[5]


def test_g7_mint_fee_split_avoids_one_micro_usdc_fee_but_costs_many_transactions(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    fee_bps = 500
    aggregate = 20  # raw USDC units; first amount with a nonzero 5% fee

    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)
        charlie_token.mint(user, aggregate, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, aggregate, sender=user)
        large_green = endaoment_psm.mintGreen(aggregate, user, False, sender=user)
        large_fee = filter_logs(endaoment_psm, "MintGreen")[-1].usdcFee
        large_paid = aggregate - charlie_token.balanceOf(user)
        after_psm_tx()

    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)
        charlie_token.mint(user, aggregate, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, aggregate, sender=user)
        split_green = 0
        split_fee = 0
        for _ in range(aggregate):
            split_green += endaoment_psm.mintGreen(1, user, False, sender=user)
            split_fee += filter_logs(endaoment_psm, "MintGreen")[-1].usdcFee
            after_psm_tx()
        split_paid = aggregate - charlie_token.balanceOf(user)

    assert large_paid == split_paid == aggregate
    assert large_fee == 1
    assert split_fee == 0
    assert split_green - large_green == ONE_GREEN // ONE_USDC


def test_g7_redeem_partial_fill_exact_drain_then_zero_inventory_reverts_before_pull(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    user = boa.env.generate_address()
    inventory = 100 * ONE_USDC
    requested_green = 200 * ONE_GREEN
    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
    green_token.transfer(user, requested_green, sender=whale)
    green_token.approve(endaoment_psm.address, requested_green, sender=user)

    supply_before = green_token.totalSupply()
    user_green_before = green_token.balanceOf(user)
    paid = endaoment_psm.redeemGreen(requested_green, user, False, sender=user)
    after_psm_tx()

    assert paid == inventory
    assert green_token.balanceOf(user) == user_green_before - 100 * ONE_GREEN
    assert green_token.totalSupply() == supply_before - 100 * ONE_GREEN
    assert charlie_token.balanceOf(endaoment_psm.address) == 0
    assert endaoment_psm.globalRedeemInterval().amount == 100 * ONE_GREEN

    state = (
        green_token.balanceOf(user),
        green_token.totalSupply(),
        green_token.allowance(user, endaoment_psm.address),
        endaoment_psm.globalRedeemInterval(),
    )
    with boa.reverts("zero amount"):
        endaoment_psm.redeemGreen(requested_green, user, False, sender=user)
    assert green_token.balanceOf(user) == state[0]
    assert green_token.totalSupply() == state[1]
    assert green_token.allowance(user, endaoment_psm.address) == state[2]
    assert endaoment_psm.globalRedeemInterval() == state[3]


def test_g7_regular_hundred_percent_redeem_fee_reverts_before_green_pull(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        green_amount = 10 * ONE_GREEN
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setRedeemFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, 10 * ONE_USDC, sender=governance.address)
        green_token.transfer(user, green_amount, sender=whale)
        green_token.approve(endaoment_psm.address, green_amount, sender=user)

        before = (
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
            len(filter_logs(endaoment_psm, "RedeemGreen")),
        )
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(green_amount, user, False, sender=user)

        assert (
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
            len(filter_logs(endaoment_psm, "RedeemGreen")),
        ) == before


def test_g7_credit_minted_green_redeems_by_the_regular_per_transaction_identity(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    credit_engine,
):
    """CreditEngine sender impersonation seeds valid GREEN, not a credit-flow audit."""
    with boa.env.anchor():
        user = boa.env.generate_address()
        green_amount = 7 * ONE_GREEN
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(endaoment_psm.address, 10 * ONE_USDC, sender=governance.address)
        green_token.mint(user, green_amount, sender=credit_engine.address)
        green_token.approve(endaoment_psm.address, green_amount, sender=user)

        user_usdc_before = charlie_token.balanceOf(user)
        supply_before = green_token.totalSupply()
        assert endaoment_psm.redeemGreen(green_amount, user, False, sender=user) == 7 * ONE_USDC
        assert charlie_token.balanceOf(user) - user_usdc_before == 7 * ONE_USDC
        assert green_token.totalSupply() == supply_before - green_amount


def test_g7_redeem_to_psm_burns_green_but_self_transfer_has_zero_net_usdc(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    user = boa.env.generate_address()
    amount = 10 * ONE_GREEN
    inventory = 25 * ONE_USDC
    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
    green_token.transfer(user, amount, sender=whale)
    green_token.approve(endaoment_psm.address, amount, sender=user)
    supply_before = green_token.totalSupply()

    returned = endaoment_psm.redeemGreen(amount, endaoment_psm.address, False, sender=user)

    assert returned == 10 * ONE_USDC
    assert charlie_token.balanceOf(endaoment_psm.address) == inventory
    assert charlie_token.balanceOf(user) == 0
    assert green_token.totalSupply() == supply_before - amount
    event = filter_logs(endaoment_psm, "RedeemGreen")[-1]
    assert event.user == endaoment_psm.address
    assert event.usdcOut == returned


def test_g7_redeem_fee_split_avoids_one_micro_usdc_fee_for_same_green_burn(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    fee_bps = 500
    aggregate_green = 20 * (ONE_GREEN // ONE_USDC)

    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setRedeemFee(fee_bps, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, ONE_USDC, sender=governance.address)
        green_token.transfer(user, aggregate_green, sender=whale)
        green_token.approve(endaoment_psm.address, aggregate_green, sender=user)
        supply_before = green_token.totalSupply()
        large_paid = endaoment_psm.redeemGreen(aggregate_green, user, False, sender=user)
        large_fee = filter_logs(endaoment_psm, "RedeemGreen")[-1].usdcFee
        large_burned = supply_before - green_token.totalSupply()
        after_psm_tx()

    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setRedeemFee(fee_bps, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, ONE_USDC, sender=governance.address)
        green_token.transfer(user, aggregate_green, sender=whale)
        green_token.approve(endaoment_psm.address, aggregate_green, sender=user)
        supply_before = green_token.totalSupply()
        split_paid = 0
        split_fee = 0
        piece = ONE_GREEN // ONE_USDC
        for _ in range(20):
            split_paid += endaoment_psm.redeemGreen(piece, user, False, sender=user)
            split_fee += filter_logs(endaoment_psm, "RedeemGreen")[-1].usdcFee
            after_psm_tx()
        split_burned = supply_before - green_token.totalSupply()

    assert large_burned == split_burned == aggregate_green
    assert large_fee == 1
    assert split_fee == 0
    assert split_paid - large_paid == 1


def test_g7_sgreen_redeem_floor_does_not_exceed_underlying_cap_and_user_view_is_wrong_unit(
    endaoment_psm,
    charlie_token,
    green_token,
    savings_green,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    user = boa.env.generate_address()
    deposit = 1_000 * ONE_GREEN
    inventory = 100 * ONE_USDC
    green_token.approve(savings_green.address, deposit, sender=whale)
    shares = savings_green.deposit(deposit, user, sender=whale)
    green_token.transfer(savings_green.address, ONE_GREEN, sender=whale)  # move PPS off 1

    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
    savings_green.approve(endaoment_psm.address, shares, sender=user)

    assert green_token.balanceOf(user) == 0
    assert savings_green.balanceOf(user) == shares
    assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
    cap = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    supply_before = green_token.totalSupply()
    paid = endaoment_psm.redeemGreen(MAX_UINT256, user, True, sender=user)
    burned = supply_before - green_token.totalSupply()

    assert burned <= cap
    assert paid == burned * ONE_USDC // ONE_GREEN
    assert paid <= inventory


def test_g7_sgreen_position_can_be_fully_redeemed_back_to_its_predeposit_baseline(
    endaoment_psm,
    charlie_token,
    green_token,
    savings_green,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        assets = 2 * ONE_GREEN
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        shares_before = savings_green.totalSupply()
        underlying_before = green_token.balanceOf(savings_green.address)
        green_token.approve(savings_green.address, assets, sender=whale)
        shares = savings_green.deposit(assets, user, sender=whale)
        charlie_token.mint(endaoment_psm.address, 2 * ONE_USDC, sender=governance.address)
        savings_green.approve(endaoment_psm.address, shares, sender=user)

        assert endaoment_psm.redeemGreen(shares, user, True, sender=user) == 2 * ONE_USDC
        assert savings_green.balanceOf(user) == 0
        assert savings_green.totalSupply() == shares_before
        assert green_token.balanceOf(savings_green.address) == underlying_before


def test_g7_missing_and_failed_price_mint_paths_fully_restore_post_pull_state(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    user = boa.env.generate_address()
    payment = 10 * ONE_USDC
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, payment, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, payment, sender=user)

    for raising_source in (False, True):
        with boa.env.anchor():
            if raising_source:
                mock_price_source.setPrice(charlie_token.address, ONE_GREEN)
                mock_price_source.setShouldRevert(charlie_token.address, True)
            else:
                mock_price_source.disablePriceFeed(charlie_token.address)

            assert endaoment_psm.getMaxUsdcAmountForMint(user, False) == payment
            before = (
                charlie_token.balanceOf(user),
                charlie_token.balanceOf(endaoment_psm.address),
                charlie_token.allowance(user, endaoment_psm.address),
                green_token.totalSupply(),
                endaoment_psm.globalMintInterval(),
            )
            with boa.reverts():
                endaoment_psm.mintGreen(payment, user, False, sender=user)
            after_psm_tx()
            assert charlie_token.balanceOf(user) == before[0]
            assert charlie_token.balanceOf(endaoment_psm.address) == before[1]
            assert charlie_token.allowance(user, endaoment_psm.address) == before[2]
            assert green_token.totalSupply() == before[3]
            assert endaoment_psm.globalMintInterval() == before[4]


def test_g7_stale_mint_capacity_then_hq_green_authorization_revocation_reverts_atomically(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    ripe_hq_deploy,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        payment = 10 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=user)
        assert endaoment_psm.getMaxUsdcAmountForMint(user, False) == payment

        reg_id = ripe_hq_deploy.getRegId(endaoment_psm.address)
        ripe_hq_deploy.initiateHqConfigChange(reg_id, False, False, False, sender=governance.address)
        boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
        assert ripe_hq_deploy.confirmHqConfigChange(reg_id, sender=governance.address)
        assert not ripe_hq_deploy.canMintGreen(endaoment_psm.address)

        before = (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.allowance(user, endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalMintInterval(),
        )
        with boa.reverts():
            endaoment_psm.mintGreen(payment, user, False, sender=user)
        assert (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.allowance(user, endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalMintInterval(),
        ) == before


def test_g7_interval_duration_accepts_first_overflowing_value_and_bricks_both_active_windows(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    """Previously an overflowing duration bricked both active interval windows.

    This test now proves mint and redeem stay callable after that duration is set.
    """
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    # At block 1, the next overflowing value is max_value itself and the setter
    # correctly rejects it. Start the window later so max - start + 1 remains an
    # accepted value. Previously that duration made the checked addition overflow.
    boa.env.time_travel(blocks=1)
    charlie_token.mint(user, 2 * ONE_USDC, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2 * ONE_USDC, sender=user)
    endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user)
    after_psm_tx()
    # Make the two active windows genuinely distinct, as they would be across
    # ordinary transactions in separate blocks.
    boa.env.time_travel(blocks=1)
    charlie_token.mint(endaoment_psm.address, ONE_USDC, sender=governance.address)
    green_token.transfer(user, ONE_GREEN, sender=whale)
    green_token.approve(endaoment_psm.address, ONE_GREEN, sender=user)
    endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user)
    after_psm_tx()

    mint_start = endaoment_psm.globalMintInterval().start
    redeem_start = endaoment_psm.globalRedeemInterval().start
    # This is safe for both windows; the later start is the tighter bound.
    safe_duration = MAX_UINT256 - max(mint_start, redeem_start)
    endaoment_psm.setNumBlocksPerInterval(safe_duration, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() < endaoment_psm.maxIntervalMint()
    assert endaoment_psm.getAvailIntervalRedemptions() < endaoment_psm.maxIntervalRedeem()

    overflowing_duration = MAX_UINT256 - min(mint_start, redeem_start) + 1
    assert overflowing_duration < MAX_UINT256
    endaoment_psm.setNumBlocksPerInterval(overflowing_duration, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() < endaoment_psm.maxIntervalMint()
    assert endaoment_psm.getAvailIntervalRedemptions() < endaoment_psm.maxIntervalRedeem()

    charlie_token.mint(endaoment_psm.address, ONE_USDC, sender=governance.address)
    green_token.transfer(user, ONE_GREEN, sender=whale)
    green_token.approve(endaoment_psm.address, ONE_GREEN, sender=user)
    assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) == ONE_GREEN
    after_psm_tx()
    assert endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user) == ONE_USDC
    after_psm_tx()


def test_g7_constructor_allows_max_interval_duration_then_bricks_after_first_mint_window(
    ripe_hq_deploy,
    charlie_token,
):
    """Previously the constructor accepted max_value duration and later overflowed.

    This test now proves the constructor rejects that duration.
    """
    with boa.env.anchor():
        with boa.reverts("invalid interval"):
            boa.load(
                "contracts/core/EndaomentPSM.vy",
                ripe_hq_deploy,
                MAX_UINT256,
                0,
                100_000 * ONE_GREEN,
                0,
                100_000 * ONE_GREEN,
                charlie_token.address,
                0,
                ZERO_ADDRESS,
                name="g7_max_duration_constructor_psm",
            )


def test_g7_max_interval_mint_accepts_overflowing_value_while_nearby_safe_value_works(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(user, ONE_USDC, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, ONE_USDC, sender=user)
    try:
        endaoment_psm.setMaxIntervalMint(MAX_SAFE_INTERVAL_MINT, sender=switchboard_charlie.address)
        assert endaoment_psm.getMaxUsdcAmountForMint() > 0
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) == ONE_GREEN
        after_psm_tx()

        with boa.reverts("invalid max"):
            endaoment_psm.setMaxIntervalMint(MAX_UINT256 - 1, sender=switchboard_charlie.address)
    finally:
        if endaoment_psm.maxIntervalMint() != 100_000 * ONE_GREEN:
            endaoment_psm.setMaxIntervalMint(100_000 * ONE_GREEN, sender=switchboard_charlie.address)


def test_g7_accepted_mint_cap_does_not_overflow_fee_gross_up(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price=1)
        endaoment_psm.setMaxIntervalMint(MAX_SAFE_INTERVAL_MINT, sender=switchboard_charlie.address)
        charlie_token.mint(user, 3 * ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 3 * ONE_USDC, sender=user)

        endaoment_psm.setMintFee(1, sender=switchboard_charlie.address)
        assert endaoment_psm.getMaxUsdcAmountForMint() > 0
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) > 0
        after_psm_tx()

        endaoment_psm.setMintFee(9_999, sender=switchboard_charlie.address)
        assert endaoment_psm.getMaxUsdcAmountForMint() > 0
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) > 0
        after_psm_tx()

        endaoment_psm.setMintFee(0, sender=switchboard_charlie.address)
        assert endaoment_psm.getMaxUsdcAmountForMint() > 0
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) > 0
        after_psm_tx()


def test_g7_near_max_redeem_cap_is_not_itself_an_overflow_dos(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setMaxIntervalRedeem(MAX_UINT256 - 1, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, ONE_USDC, sender=governance.address)
        green_token.transfer(user, ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, ONE_GREEN, sender=user)

        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == ONE_GREEN
        assert endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user) == ONE_USDC
        after_psm_tx()


def test_g7_eight_decimal_payment_token_regular_redeem_underpays_by_one_hundred_x(
    ripe_hq_deploy,
    endaoment_psm,
    charlie_token,
    delta_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    with boa.env.anchor():
        assert delta_token.decimals() == 8
        with boa.reverts("usdc must be 6 decimals"):
            boa.load(
                "contracts/core/EndaomentPSM.vy",
                ripe_hq_deploy,
                100,
                0,
                100_000 * ONE_GREEN,
                0,
                100_000 * ONE_GREEN,
                delta_token.address,
                0,
                ZERO_ADDRESS,
                name="g7_psm_8dp",
            )

        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, ONE_USDC, sender=user)
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) == ONE_GREEN
        after_psm_tx()
        green_token.approve(endaoment_psm.address, ONE_GREEN, sender=user)
        assert endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user) == ONE_USDC
        after_psm_tx()


def test_g7_interval_reconfiguration_is_global_independent_and_vault_skips_do_not_write_it(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        vault = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setNumBlocksPerInterval(10, sender=switchboard_charlie.address)
        endaoment_psm.setMaxIntervalMint(100 * ONE_GREEN, sender=switchboard_charlie.address)
        endaoment_psm.setMaxIntervalRedeem(100 * ONE_GREEN, sender=switchboard_charlie.address)
        charlie_token.mint(user, 90 * ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 90 * ONE_USDC, sender=user)

        assert endaoment_psm.mintGreen(60 * ONE_USDC, user, False, sender=user) == 60 * ONE_GREEN
        after_psm_tx()
        green_token.approve(endaoment_psm.address, 60 * ONE_GREEN, sender=user)
        assert endaoment_psm.redeemGreen(60 * ONE_GREEN, user, False, sender=user) == 60 * ONE_USDC
        after_psm_tx()
        mint_window = endaoment_psm.globalMintInterval()
        redeem_window = endaoment_psm.globalRedeemInterval()

        endaoment_psm.setMaxIntervalMint(50 * ONE_GREEN, sender=switchboard_charlie.address)
        endaoment_psm.setMaxIntervalRedeem(50 * ONE_GREEN, sender=switchboard_charlie.address)
        assert endaoment_psm.getAvailIntervalMint() == 0
        assert endaoment_psm.getAvailIntervalRedemptions() == 0
        assert endaoment_psm.globalMintInterval() == mint_window
        assert endaoment_psm.globalRedeemInterval() == redeem_window

        endaoment_psm.setMaxIntervalMint(90 * ONE_GREEN, sender=switchboard_charlie.address)
        endaoment_psm.setMaxIntervalRedeem(90 * ONE_GREEN, sender=switchboard_charlie.address)
        assert endaoment_psm.getAvailIntervalMint() == 30 * ONE_GREEN
        assert endaoment_psm.getAvailIntervalRedemptions() == 30 * ONE_GREEN

        # Duration changes do not reset either stored window.  A one-block
        # duration expires exactly at start + 1; a later ten-block setting
        # keeps the next windows active one block later.
        endaoment_psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)
        boa.env.time_travel(blocks=1)
        assert endaoment_psm.getAvailIntervalMint() == 90 * ONE_GREEN
        assert endaoment_psm.getAvailIntervalRedemptions() == 90 * ONE_GREEN

        assert endaoment_psm.mintGreen(10 * ONE_USDC, user, False, sender=user) == 10 * ONE_GREEN
        after_psm_tx()
        green_token.approve(endaoment_psm.address, 10 * ONE_GREEN, sender=user)
        assert endaoment_psm.redeemGreen(10 * ONE_GREEN, user, False, sender=user) == 10 * ONE_USDC
        after_psm_tx()
        endaoment_psm.setNumBlocksPerInterval(10, sender=switchboard_charlie.address)
        boa.env.time_travel(blocks=1)
        assert endaoment_psm.getAvailIntervalMint() == 80 * ONE_GREEN
        assert endaoment_psm.getAvailIntervalRedemptions() == 80 * ONE_GREEN

        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setEarnVault(vault, True)
        before_vault_mint = endaoment_psm.globalMintInterval()
        before_vault_redeem = endaoment_psm.globalRedeemInterval()
        assert endaoment_psm.mintGreen(20 * ONE_USDC, vault, False, sender=user) == 20 * ONE_GREEN
        after_psm_tx()
        green_token.transfer(user, 20 * ONE_GREEN, sender=vault)
        green_token.approve(endaoment_psm.address, 20 * ONE_GREEN, sender=user)
        assert endaoment_psm.redeemGreen(20 * ONE_GREEN, vault, False, sender=user) == 20 * ONE_USDC
        assert endaoment_psm.globalMintInterval() == before_vault_mint
        assert endaoment_psm.globalRedeemInterval() == before_vault_redeem

        mock_undy_v2.setEarnVault(vault, False)
        mock_undy_v2.setAllAddressesAreVaults(True)


@pytest.mark.parametrize(
    "price",
    (95 * ONE_GREEN // 100, ONE_GREEN, 105 * ONE_GREEN // 100),
)
@pytest.mark.parametrize("fee_bps", (0, 500))
@pytest.mark.parametrize("mint_to_vault", (False, True))
@pytest.mark.parametrize("redeem_to_vault", (False, True))
def test_g7_regular_and_vault_recipient_round_trip_matrix_matches_min_max_and_fee_formulae(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    price,
    fee_bps,
    mint_to_vault,
    redeem_to_vault,
):
    """Vault-address ownership is intentionally math-only in this 24-case matrix."""
    with boa.env.anchor():
        payer = boa.env.generate_address()
        vault = boa.env.generate_address()
        payment = 1_000 * ONE_USDC
        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setEarnVault(vault, True)
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)
        if fee_bps:
            endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)
            endaoment_psm.setRedeemFee(fee_bps, sender=switchboard_charlie.address)
        charlie_token.mint(payer, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=payer)

        mint_recipient = vault if mint_to_vault else payer
        mint_fee = 0 if mint_to_vault else payment * fee_bps // HUNDRED_PERCENT
        mint_after_fee = payment - mint_fee
        expected_green = min(
            price * mint_after_fee // ONE_USDC,
            mint_after_fee * ONE_GREEN // ONE_USDC,
        )
        assert endaoment_psm.mintGreen(payment, mint_recipient, False, sender=payer) == expected_green
        after_psm_tx()
        assert green_token.balanceOf(mint_recipient) == expected_green
        if mint_to_vault:
            # This sender impersonation only puts the math under the caller's
            # control; it does not claim a real Underscore beneficiary path.
            green_token.transfer(payer, expected_green, sender=vault)
        green_token.approve(endaoment_psm.address, expected_green, sender=payer)

        redeem_recipient = vault if redeem_to_vault else payer
        price_desk_leg = expected_green * ONE_USDC // price
        one_to_one_leg = expected_green * ONE_USDC // ONE_GREEN
        gross_usdc = max(price_desk_leg, one_to_one_leg) if redeem_to_vault else min(price_desk_leg, one_to_one_leg)
        redeem_fee = 0 if redeem_to_vault else gross_usdc * fee_bps // HUNDRED_PERCENT
        expected_payout = gross_usdc - redeem_fee
        recipient_before = charlie_token.balanceOf(redeem_recipient)
        assert endaoment_psm.redeemGreen(expected_green, redeem_recipient, False, sender=payer) == expected_payout

        assert charlie_token.balanceOf(redeem_recipient) - recipient_before == expected_payout
        assert charlie_token.balanceOf(endaoment_psm.address) == payment - expected_payout
        assert expected_payout <= payment

        mock_undy_v2.setEarnVault(vault, False)
        mock_undy_v2.setAllAddressesAreVaults(True)


def test_g7_sgreen_mint_threshold_wraps_only_above_one_green_and_resets_psm_allowance(
    endaoment_psm,
    charlie_token,
    green_token,
    savings_green,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, 3 * ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 3 * ONE_USDC, sender=user)

        assert endaoment_psm.mintGreen(ONE_USDC, user, True, sender=user) == ONE_GREEN
        raw_event = filter_logs(endaoment_psm, "MintGreen")[-1]
        after_psm_tx()
        assert green_token.balanceOf(user) == ONE_GREEN
        assert savings_green.balanceOf(user) == 0
        assert not raw_event.receivedSavingsGreen

        assert endaoment_psm.mintGreen(2 * ONE_USDC, user, True, sender=user) == 2 * ONE_GREEN
        wrapped_event = filter_logs(endaoment_psm, "MintGreen")[-1]
        assert green_token.balanceOf(user) == ONE_GREEN
        assert savings_green.balanceOf(user) == 2 * ONE_GREEN
        assert green_token.balanceOf(endaoment_psm.address) == 0
        assert green_token.allowance(endaoment_psm.address, savings_green.address) == 0
        assert wrapped_event.receivedSavingsGreen


def test_g7_sgreen_transfer_or_underlying_green_pause_failures_restore_everything(
    endaoment_psm,
    charlie_token,
    green_token,
    savings_green,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        green_amount = 100 * ONE_GREEN
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(endaoment_psm.address, 100 * ONE_USDC, sender=governance.address)
        green_token.approve(savings_green.address, green_amount, sender=whale)
        shares = savings_green.deposit(green_amount, user, sender=whale)
        savings_green.approve(endaoment_psm.address, shares, sender=user)

        before = (
            savings_green.balanceOf(user),
            savings_green.allowance(user, endaoment_psm.address),
            green_token.balanceOf(savings_green.address),
            green_token.balanceOf(endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        )
        savings_green.pause(True, sender=governance.address)
        with boa.reverts():
            endaoment_psm.redeemGreen(shares, user, True, sender=user)
        after_psm_tx()
        assert (
            savings_green.balanceOf(user),
            savings_green.allowance(user, endaoment_psm.address),
            green_token.balanceOf(savings_green.address),
            green_token.balanceOf(endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == before

        savings_green.pause(False, sender=governance.address)
        green_token.pause(True, sender=governance.address)
        with boa.reverts():
            endaoment_psm.redeemGreen(shares, user, True, sender=user)
        assert (
            savings_green.balanceOf(user),
            savings_green.allowance(user, endaoment_psm.address),
            green_token.balanceOf(savings_green.address),
            green_token.balanceOf(endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == before


def test_g7_regular_sender_allowlists_flags_pause_and_green_mint_gate(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        with boa.reverts("minting disabled"):
            endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user)
        after_psm_tx()
        with boa.reverts("redemption disabled"):
            endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user)
        after_psm_tx()
        with boa.reverts("cannot mint"):
            green_token.mint(user, ONE_GREEN, sender=user)

        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, 10 * ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 10 * ONE_USDC, sender=user)
        endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
        with boa.reverts("not on mint allowlist"):
            endaoment_psm.mintGreen(10 * ONE_USDC, user, False, sender=user)
        after_psm_tx()
        endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)
        assert endaoment_psm.mintGreen(10 * ONE_USDC, user, False, sender=user) == 10 * ONE_GREEN
        after_psm_tx()

        green_token.approve(endaoment_psm.address, 10 * ONE_GREEN, sender=user)
        endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)
        with boa.reverts("not on redeem allowlist"):
            endaoment_psm.redeemGreen(10 * ONE_GREEN, user, False, sender=user)
        after_psm_tx()
        endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)
        assert endaoment_psm.redeemGreen(10 * ONE_GREEN, user, False, sender=user) == 10 * ONE_USDC
        after_psm_tx()

        endaoment_psm.pause(True, sender=switchboard_charlie.address)
        with boa.reverts("contract paused"):
            endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user)
        after_psm_tx()
        with boa.reverts("contract paused"):
            endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user)
        after_psm_tx()


def test_g7_green_pause_and_psm_blacklist_fail_at_real_preburn_sites_with_full_rollback(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        payment = 10 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=user)
        charlie_token.mint(endaoment_psm.address, payment, sender=governance.address)
        green_token.transfer(user, 2 * ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, 2 * ONE_GREEN, sender=user)

        mint_before = (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.allowance(user, endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalMintInterval(),
        )
        green_token.pause(True, sender=governance.address)
        with boa.reverts():
            endaoment_psm.mintGreen(payment, user, False, sender=user)
        after_psm_tx()
        assert (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.allowance(user, endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalMintInterval(),
        ) == mint_before

        redeem_before = (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        )
        with boa.reverts():
            endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user)
        after_psm_tx()
        assert (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == redeem_before

        green_token.pause(False, sender=governance.address)
        green_token.setBlacklist(endaoment_psm.address, True, sender=switchboard.address)
        with boa.reverts():
            endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user)
        assert (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == redeem_before


@pytest.mark.parametrize("mutation", ("price", "fee", "allowlist", "disable"))
def test_g7_mint_capacity_view_is_not_a_quote_after_one_config_mutation(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    mutation,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        payment = 100 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=user)
        assert endaoment_psm.getMaxUsdcAmountForMint(user, False) == payment
        before = (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.allowance(user, endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalMintInterval(),
        )

        if mutation == "price":
            mock_price_source.setPrice(charlie_token.address, 95 * ONE_GREEN // 100)
            assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 95 * ONE_GREEN
        elif mutation == "fee":
            endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
            assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 95 * ONE_GREEN
        elif mutation == "allowlist":
            endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
            with boa.reverts("not on mint allowlist"):
                endaoment_psm.mintGreen(payment, user, False, sender=user)
            after_psm_tx()
            assert (
                charlie_token.balanceOf(user),
                charlie_token.balanceOf(endaoment_psm.address),
                charlie_token.allowance(user, endaoment_psm.address),
                green_token.balanceOf(user),
                green_token.totalSupply(),
                endaoment_psm.globalMintInterval(),
            ) == before
        else:
            endaoment_psm.setCanMint(False, sender=switchboard_charlie.address)
            with boa.reverts("minting disabled"):
                endaoment_psm.mintGreen(payment, user, False, sender=user)
            after_psm_tx()
            assert (
                charlie_token.balanceOf(user),
                charlie_token.balanceOf(endaoment_psm.address),
                charlie_token.allowance(user, endaoment_psm.address),
                green_token.balanceOf(user),
                green_token.totalSupply(),
                endaoment_psm.globalMintInterval(),
            ) == before


@pytest.mark.parametrize("mutation", ("price", "fee", "interval"))
def test_g7_redeem_capacity_view_is_not_a_quote_after_one_mutation(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
    mutation,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        other = boa.env.generate_address()
        inventory = 1_000 * ONE_USDC if mutation == "interval" else 100 * ONE_USDC
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        if mutation == "interval":
            endaoment_psm.setMaxIntervalRedeem(100 * ONE_GREEN, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
        green_token.transfer(user, 100 * ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, 100 * ONE_GREEN, sender=user)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 100 * ONE_GREEN

        if mutation == "price":
            mock_price_source.setPrice(charlie_token.address, 105 * ONE_GREEN // 100)
            assert endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user) == 95_238_095
        elif mutation == "fee":
            endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)
            assert endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user) == 95 * ONE_USDC
        else:
            green_token.transfer(other, 60 * ONE_GREEN, sender=whale)
            green_token.approve(endaoment_psm.address, 60 * ONE_GREEN, sender=other)
            assert endaoment_psm.redeemGreen(60 * ONE_GREEN, other, False, sender=other) == 60 * ONE_USDC
            after_psm_tx()
            assert endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user) == 40 * ONE_USDC
            assert green_token.balanceOf(user) == 60 * ONE_GREEN


def test_g7_vault_boolean_in_capacity_view_does_not_make_an_eoa_a_vault_flow(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setMaxIntervalMint(10 * ONE_GREEN, sender=switchboard_charlie.address)
        charlie_token.mint(user, 100 * ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 100 * ONE_USDC, sender=user)

        assert endaoment_psm.getMaxUsdcAmountForMint(user, True) == 100 * ONE_USDC
        assert endaoment_psm.getMaxUsdcAmountForMint(user, False) == 10 * ONE_USDC
        assert endaoment_psm.mintGreen(100 * ONE_USDC, user, False, sender=user) == 10 * ONE_GREEN
        after_psm_tx()
        assert charlie_token.balanceOf(user) == 90 * ONE_USDC

        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setMaxIntervalRedeem(10 * ONE_GREEN, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, 90 * ONE_USDC, sender=governance.address)
        green_token.transfer(user, 90 * ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, 100 * ONE_GREEN, sender=user)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, True) == 100 * ONE_GREEN
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 10 * ONE_GREEN
        assert endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user) == 10 * ONE_USDC


def test_g7_missing_price_redeem_view_is_zero_and_stops_before_green_pull(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        payment = 10 * ONE_USDC
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, payment, sender=governance.address)
        green_token.transfer(user, 10 * ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, 10 * ONE_GREEN, sender=user)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
        before = (
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        )
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(10 * ONE_GREEN, user, False, sender=user)
        assert (
            charlie_token.balanceOf(endaoment_psm.address),
            green_token.balanceOf(user),
            green_token.allowance(user, endaoment_psm.address),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == before
