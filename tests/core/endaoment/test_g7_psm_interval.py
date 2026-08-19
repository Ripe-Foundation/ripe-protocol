"""Group 7 never-skip #4: interval passage, reconfiguration, rounding."""

import boa
import pytest

from constants import ZERO_ADDRESS
from core.endaoment.g7_psm_helpers import (
    E18,
    ONE_DAY_BLOCKS,
    SIX,
    after_psm_tx,
    enable_mint,
    enable_redeem,
    fund_usdc,
    reset_psm_regular,
    set_usdc_price,
)


def _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token):
    reset_psm_regular(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2)
    set_usdc_price(mock_price_source, charlie_token, E18)
    enable_mint(endaoment_psm, switchboard_charlie)
    enable_redeem(endaoment_psm, switchboard_charlie)


def test_g7_interval_exact_expiry_is_fresh(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
    credit_engine,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, 300 * SIX, governance)
    charlie_token.approve(endaoment_psm.address, 300 * SIX, sender=user)
    endaoment_psm.mintGreen(100 * SIX, sender=user)
    after_psm_tx()
    start = endaoment_psm.globalMintInterval().start
    duration = endaoment_psm.numBlocksPerInterval()
    assert duration == ONE_DAY_BLOCKS

    # One block before expiry: still active.
    boa.env.time_travel(blocks=duration - 1)
    assert boa.env.evm.patch.block_number == start + duration - 1
    assert endaoment_psm.getAvailIntervalMint() == 100_000 * E18 - 100 * E18
    endaoment_psm.mintGreen(50 * SIX, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalMintInterval().start == start
    assert endaoment_psm.globalMintInterval().amount == 150 * E18

    # Exact expiry (start + duration): fresh interval.
    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == start + duration
    assert endaoment_psm.getAvailIntervalMint() == 100_000 * E18
    endaoment_psm.mintGreen(25 * SIX, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalMintInterval().start == start + duration
    assert endaoment_psm.globalMintInterval().amount == 25 * E18

    # One after: still the new window.
    boa.env.time_travel(blocks=1)
    assert endaoment_psm.globalMintInterval().start == start + duration

    fund_usdc(charlie_token, endaoment_psm.address, 300 * SIX, governance)
    green_token.mint(user, 300 * E18, sender=credit_engine.address)
    green_token.approve(endaoment_psm.address, 300 * E18, sender=user)
    endaoment_psm.redeemGreen(100 * E18, sender=user)
    after_psm_tx()
    redeem_start = endaoment_psm.globalRedeemInterval().start
    redeem_duration = endaoment_psm.numBlocksPerInterval()
    boa.env.time_travel(blocks=redeem_duration - 1)
    assert endaoment_psm.getAvailIntervalRedemptions() == 100_000 * E18 - 100 * E18
    endaoment_psm.redeemGreen(50 * E18, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalRedeemInterval().start == redeem_start
    boa.env.time_travel(blocks=1)
    assert endaoment_psm.getAvailIntervalRedemptions() == 100_000 * E18
    endaoment_psm.redeemGreen(25 * E18, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalRedeemInterval().start == redeem_start + redeem_duration


def test_g7_mint_and_redeem_intervals_are_independent(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
    credit_engine,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, 100 * SIX, governance)
    charlie_token.approve(endaoment_psm.address, 100 * SIX, sender=user)
    fund_usdc(charlie_token, endaoment_psm.address, 500 * SIX, governance)
    green_token.mint(user, 100 * E18, sender=credit_engine.address)
    green_token.approve(endaoment_psm.address, 100 * E18, sender=user)

    endaoment_psm.mintGreen(40 * SIX, sender=user)
    after_psm_tx()
    mint_iv = endaoment_psm.globalMintInterval()
    endaoment_psm.redeemGreen(40 * E18, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalMintInterval() == mint_iv
    assert endaoment_psm.globalRedeemInterval().amount == 40 * E18

    endaoment_psm.setMaxIntervalMint(1_000 * E18, sender=switchboard_charlie.address)
    assert endaoment_psm.globalMintInterval().start == mint_iv.start
    assert endaoment_psm.globalMintInterval().amount == mint_iv.amount
    assert endaoment_psm.globalRedeemInterval().amount == 40 * E18
    assert endaoment_psm.getAvailIntervalMint() == 1_000 * E18 - 40 * E18

    endaoment_psm.setMaxIntervalMint(20 * E18, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 0  # consumed 40 > new max 20
    if endaoment_psm.maxIntervalMint() != 100_000 * E18:
        endaoment_psm.setMaxIntervalMint(100_000 * E18, sender=switchboard_charlie.address)


def test_g7_lower_raise_shorten_lengthen_duration(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, 100 * SIX, governance)
    charlie_token.approve(endaoment_psm.address, 100 * SIX, sender=user)
    endaoment_psm.mintGreen(30 * SIX, sender=user)
    after_psm_tx()
    start = endaoment_psm.globalMintInterval().start

    endaoment_psm.setMaxIntervalMint(200 * E18, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 170 * E18

    # Same block, duration=1: start+1 > now, window still active.
    endaoment_psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 170 * E18
    boa.env.time_travel(blocks=1)
    assert endaoment_psm.getAvailIntervalMint() == 200 * E18  # expired
    # Lengthen: stored start + 43200 is still in the future; consumed 30 remains.
    endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS, sender=switchboard_charlie.address)
    assert endaoment_psm.globalMintInterval().start == start
    assert endaoment_psm.getAvailIntervalMint() == 170 * E18

    endaoment_psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)
    boa.env.time_travel(blocks=1)
    endaoment_psm.mintGreen(10 * SIX, sender=user)
    after_psm_tx()
    assert endaoment_psm.globalMintInterval().amount == 10 * E18
    endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(100_000 * E18, sender=switchboard_charlie.address)


def test_g7_max_value_minus_one_duration_overflows_ordinary_interval(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
    credit_engine,
):
    """Previously `max_value - 1` overflowed ordinary interval add and bricked mint/redeem.

    This test now proves views and both paths stay callable at that duration.
    """
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, 10 * SIX, governance)
    charlie_token.approve(endaoment_psm.address, 10 * SIX, sender=user)
    endaoment_psm.mintGreen(1 * SIX, sender=user)
    after_psm_tx()
    start = endaoment_psm.globalMintInterval().start
    assert start >= 2
    fund_usdc(charlie_token, endaoment_psm.address, 2 * SIX, governance)
    green_token.mint(user, 2 * E18, sender=credit_engine.address)
    green_token.approve(endaoment_psm.address, 2 * E18, sender=user)
    endaoment_psm.redeemGreen(1 * E18, sender=user)
    after_psm_tx()
    try:
        endaoment_psm.setNumBlocksPerInterval(2**256 - 2, sender=switchboard_charlie.address)
        assert endaoment_psm.getAvailIntervalMint() == 100_000 * E18 - 1 * E18
        assert endaoment_psm.getAvailIntervalRedemptions() == 100_000 * E18 - 1 * E18
        assert endaoment_psm.mintGreen(1 * SIX, sender=user) == 1 * E18
        after_psm_tx()
        assert endaoment_psm.redeemGreen(1 * E18, sender=user) == 1 * SIX
        after_psm_tx()
    finally:
        if endaoment_psm.numBlocksPerInterval() != ONE_DAY_BLOCKS:
            endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS, sender=switchboard_charlie.address)


def test_g7_max_interval_overflow_ordinary_view_reverts_vault_view_does_not(
    endaoment_psm,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    mock_price_source,
    charlie_token,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    try:
        with boa.reverts("invalid max"):
            endaoment_psm.setMaxIntervalMint(2**256 - 2, sender=switchboard_charlie.address)
        endaoment_psm.setMaxIntervalMint(50_000 * E18, sender=switchboard_charlie.address)
        assert endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False) > 0
        assert endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, True) == 2**256 - 1
    finally:
        if endaoment_psm.maxIntervalMint() != 100_000 * E18:
            endaoment_psm.setMaxIntervalMint(100_000 * E18, sender=switchboard_charlie.address)


def test_g7_quote_bounds_ordinary_execute(
    endaoment_psm,
    charlie_token,
    green_token,
    savings_green,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
    credit_engine,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, 10_000 * SIX, governance)
    charlie_token.approve(endaoment_psm.address, 10_000 * SIX, sender=user)
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    avail = endaoment_psm.getAvailIntervalMint()
    paid_before = charlie_token.balanceOf(user)
    green = endaoment_psm.mintGreen(10_000 * SIX, sender=user)
    after_psm_tx()
    assert paid_before - charlie_token.balanceOf(user) <= max_usdc
    assert green <= avail

    fund_usdc(charlie_token, endaoment_psm.address, 5_000 * SIX, governance)
    green_token.mint(user, 2_000 * E18, sender=credit_engine.address)
    green_token.approve(endaoment_psm.address, 2_000 * E18, sender=user)
    max_green = endaoment_psm.getMaxRedeemableGreenAmount(user, False)
    burned_before = green_token.balanceOf(user)
    endaoment_psm.redeemGreen(2_000 * E18, sender=user)
    after_psm_tx()
    assert burned_before - green_token.balanceOf(user) <= max_green


@pytest.mark.parametrize("price,fee_bps,usdc", [
    (E18, 0, 1),
    (E18, 0, SIX),
    (E18, 1, 10_000),
    (E18, 1, 9_999),
    (int(0.95 * E18), 500, 100 * SIX),
    (int(1.05 * E18), 500, 100 * SIX),
])
def test_g7_dust_and_fee_grid_unit_correct(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    governance,
    mock_price_source,
    price,
    fee_bps,
    usdc,
):
    _prep(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2, mock_price_source, charlie_token)
    set_usdc_price(mock_price_source, charlie_token, price)
    if fee_bps:
        endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)
    user = boa.env.generate_address()
    fund_usdc(charlie_token, user, usdc, governance)
    charlie_token.approve(endaoment_psm.address, usdc, sender=user)
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    if max_usdc == 0:
        with boa.reverts("zero amount"):
            endaoment_psm.mintGreen(usdc, sender=user)
        after_psm_tx()
        return
    paid_before = charlie_token.balanceOf(user)
    avail = endaoment_psm.getAvailIntervalMint()
    green = endaoment_psm.mintGreen(usdc, sender=user)
    after_psm_tx()
    assert paid_before - charlie_token.balanceOf(user) <= max_usdc
    assert green <= avail
    assert green > 0
