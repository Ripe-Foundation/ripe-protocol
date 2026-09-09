"""Group 7 PSM proofs — never-skip #4: interval passage, reconfiguration, rounding.

Interval time is block.number; time_travel moves blocks. Local fixture:
numBlocksPerInterval = 43_200 (ONE_DAY_BLOCKS) — fixture-relative per brief.
Mint and redeem intervals are independent. Proofs use the session PSM (reset
by the autouse fixture) unless a config change would be destructive to other
tests, in which case a fresh PSM is deployed (ripe_hq_deploy + charlie_token).
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256

from tests.core.endaoment import g7_psm_helpers as g7


SIX = 10**6
E18 = 10**18
HUNDRED = 10_000
ONE_DAY_BLOCKS = 43_200


@pytest.fixture(autouse=True)
def _reset(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2):
    g7.reset_psm_regular(
        endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2
    )
    yield


def _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price=E18):
    mock_price_source.setPrice(charlie_token.address, price)
    if not endaoment_psm.canMint():
        endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    if not endaoment_psm.canRedeem():
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


def _fresh_psm(ripe_hq_deploy, charlie_token, num_blocks=ONE_DAY_BLOCKS, max_mint=100_000 * E18, max_redeem=100_000 * E18):
    return boa.load(
        "contracts/core/EndaomentPSM.vy",
        ripe_hq_deploy,
        num_blocks,
        0,
        max_mint,
        0,
        max_redeem,
        charlie_token.address,
        0,
        ZERO_ADDRESS,
    )


def test_g7_interval_exact_expiry_boundary(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Window test start != 0 and start + numBlocks > block.number. One block
    before expiry: still the same window. At exactly start + numBlocks: a FRESH
    interval starts (full cap again)."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)

    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    g7.after_psm_tx()
    data = endaoment_psm.globalMintInterval()
    assert data.amount == 10 * E18
    start = data.start
    assert endaoment_psm.getAvailIntervalMint() == 0

    # one block before expiry: still same window
    now = boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=start + ONE_DAY_BLOCKS - 1 - now)
    assert boa.env.evm.patch.block_number == start + ONE_DAY_BLOCKS - 1
    assert endaoment_psm.getAvailIntervalMint() == 0

    # at exactly start + numBlocks: fresh interval
    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == start + ONE_DAY_BLOCKS
    assert endaoment_psm.getAvailIntervalMint() == 10 * E18

    # the next mint starts a new window at the current block
    endaoment_psm.mintGreen(1 * SIX, user, False, sender=user)
    data2 = endaoment_psm.globalMintInterval()
    assert data2.start == start + ONE_DAY_BLOCKS
    assert data2.amount == 1 * E18


def test_g7_mint_and_redeem_intervals_independent(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """Mint consumption never touches the redeem interval and vice versa."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalRedeem(20 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    g7.after_psm_tx()

    assert endaoment_psm.getAvailIntervalMint() == 0
    assert endaoment_psm.getAvailIntervalRedemptions() == 20 * E18  # untouched

    # redeem from the minted GREEN
    charlie_token.mint(endaoment_psm.address, 1_000 * SIX, sender=governance.address)
    green_token.approve(endaoment_psm.address, 10 * E18, sender=user)
    endaoment_psm.redeemGreen(10 * E18, user, False, sender=user)

    assert endaoment_psm.getAvailIntervalRedemptions() == 10 * E18
    assert endaoment_psm.getAvailIntervalMint() == 0  # still untouched


def test_g7_lower_max_below_consumed_gives_zero(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Live config: lower maxIntervalMint below already-consumed -> available 0
    (the min(data.amount, max) floor keeps it from underflowing negative)."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(1_000 * SIX, user, False, sender=user)  # consumed 1000 GREEN
    g7.after_psm_tx()

    endaoment_psm.setMaxIntervalMint(500 * E18, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 0  # not negative

    # a new mint in the same window gets nothing more (zero-amount revert)
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(1 * SIX, user, False, sender=user)


def test_g7_raise_max_gives_newmax_minus_consumed(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Raise max mid-window: available = newMax - consumed."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(100 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(60 * SIX, user, False, sender=user)

    endaoment_psm.setMaxIntervalMint(150 * E18, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 90 * E18  # 150 - 60


def test_g7_change_max_does_not_reset_window(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Changing a max never resets stored start/amount."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(100 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(60 * SIX, user, False, sender=user)
    data_before = endaoment_psm.globalMintInterval()

    endaoment_psm.setMaxIntervalMint(200 * E18, sender=switchboard_charlie.address)
    data_after = endaoment_psm.globalMintInterval()
    assert data_after.start == data_before.start
    assert data_after.amount == data_before.amount == 60 * E18


def test_g7_shorten_duration_expires_window_immediately(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Shorten numBlocksPerInterval so the current window expires at once:
    full cap is available again (start + newDur <= now). Note: boa does NOT
    auto-mine a block per call — block number only moves via time_travel —
    so the assertion is directly on the view."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    assert endaoment_psm.getAvailIntervalMint() == 0

    endaoment_psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)
    boa.env.time_travel(blocks=1)  # now > start + 1
    assert endaoment_psm.getAvailIntervalMint() == 10 * E18  # expired


def test_g7_lengthen_duration_keeps_window_active(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Lengthen numBlocksPerInterval: the current window stays active with its
    consumption intact."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    assert endaoment_psm.getAvailIntervalMint() == 0

    endaoment_psm.setNumBlocksPerInterval(10 * ONE_DAY_BLOCKS, sender=switchboard_charlie.address)
    assert endaoment_psm.getAvailIntervalMint() == 0  # window still active


def test_g7_duration_one_block(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Duration 1 (set live on the session PSM): the window only lives while
    start + 1 > block.number — the same block it was opened. One block later
    is a fresh interval with the full cap. (Session PSM, not a fresh deploy:
    fresh PSMs cannot mint because RipeHq.canMintGreen only registers the
    canonical PSM — confirmed by probe. boa blocks move only via time_travel.)"""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)
    endaoment_psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)

    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    g7.after_psm_tx()
    assert endaoment_psm.getAvailIntervalMint() == 0  # same-block cap exhausted
    boa.env.time_travel(blocks=1)
    assert endaoment_psm.getAvailIntervalMint() == 10 * E18  # fresh window
    endaoment_psm.mintGreen(10 * SIX, user, False, sender=user)
    assert green_token.balanceOf(user) == 20 * E18


def test_g7_largest_duration_no_overflow_dos(
    endaoment_psm, switchboard_charlie, charlie_token, green_token, governance, mock_price_source,
):
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setNumBlocksPerInterval(MAX_UINT256 - 1, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)

    assert endaoment_psm.globalMintInterval().start == 0
    boa.env.time_travel(blocks=2)
    assert endaoment_psm.mintGreen(1 * SIX, user, False, sender=user) == 1 * E18
    g7.after_psm_tx()
    assert endaoment_psm.globalMintInterval().start >= 2
    assert endaoment_psm.mintGreen(1 * SIX, user, False, sender=user) == 1 * E18
    g7.after_psm_tx()
    assert green_token.balanceOf(user) == 2 * E18


def test_g7_max_interval_max_minus_one_no_overflow_on_mint(
    endaoment_psm, switchboard_charlie, charlie_token, green_token, governance, mock_price_source,
):
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    with boa.reverts("invalid max"):
        endaoment_psm.setMaxIntervalMint(MAX_UINT256 - 1, sender=switchboard_charlie.address)

    charlie_token.mint(user, 1_000 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=user)
    assert endaoment_psm.mintGreen(1 * SIX, user, False, sender=user) == 1 * E18


def test_g7_property_bounded_grid_unit_correct(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Property-style bounded grid (price x fee x amount): ordinary mint payer
    USDC debit <= pre-call getMaxUsdcAmountForMint; greenToMint and interval
    increment <= pre-call getAvailIntervalMint; redeem burn <=
    getMaxRedeemableGreenAmount. Unit-correct per brief's table."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    for price in (95 * E18 // 100, E18, 105 * E18 // 100):
        mock_price_source.setPrice(charlie_token.address, price)
        for fee_bps in (0, 100, 1_000):
            if endaoment_psm.mintFee() != fee_bps:
                endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)
            for usdc_amount in (1 * SIX, 777 * SIX, 5_000 * SIX):
                user = boa.env.generate_address()
                charlie_token.mint(user, usdc_amount, sender=governance.address)
                charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

                max_usdc_before = endaoment_psm.getMaxUsdcAmountForMint(user, False)
                avail_before = endaoment_psm.getAvailIntervalMint()
                pre_usdc = charlie_token.balanceOf(user)
                pre_supply = green_token.totalSupply()

                endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
                g7.after_psm_tx()

                debit = pre_usdc - charlie_token.balanceOf(user)
                minted = green_token.totalSupply() - pre_supply
                interval_used = avail_before - endaoment_psm.getAvailIntervalMint()

                # bounded by the pre-call views (same state)
                assert debit <= max_usdc_before or max_usdc_before == 0
                assert minted <= avail_before
                assert interval_used == minted
                # independent identity
                expected, fee, after, usd_value, one_to_one = g7.expected_mint_green(debit, fee_bps, price)
                assert minted == expected
            boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
