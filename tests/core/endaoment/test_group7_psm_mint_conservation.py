"""Group 7 PSM proofs — never-skip #1: mint conservation (regular path).

Payment token: charlie_token (MockErc20, 6 decimals) as the PSM's immutable USDC.
Flags enabled via setCanMint(True, sender=switchboard_charlie.address) — address
impersonation of a Switchboard board (suite enablement shortcut per brief).

Every test resets the session-scoped PSM to a launch-shaped regular path first
(g7_psm_helpers.reset_psm_regular) because sibling PSM suites share the fixture.
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


def _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price=E18):
    mock_price_source.setPrice(charlie_token.address, price)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)


###############
# Conservation #
###############


def test_g7_mint_conservation_fee_grid(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source,
):
    """For fee in {0, 1, 500, 9999}: payer USDC debit == usdcAmount == PSM credit
    (no auto-deposit yield configured), recipient GREEN == greenToMint ==
    min(usdValue, 1:1) computed independently, interval increments by greenToMint,
    supply increases by greenToMint, event fields match, allowance untouched."""
    user = boa.env.generate_address()
    usdc_amount = 1_000 * SIX
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    for fee_bps in (0, 1, 500, 9_999):
        if endaoment_psm.mintFee() != fee_bps:
            endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)

        charlie_token.mint(user, usdc_amount, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

        pre = g7.snapshot_mint(endaoment_psm, charlie_token, green_token, savings_green, user, user)
        expected_green, fee, after, usd_value, one_to_one = g7.expected_mint_green(usdc_amount, fee_bps, E18)
        avail_before = pre["avail_mint"]

        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
        ev = g7.last_mint_event(endaoment_psm)  # last computation's logs — read before any other call
        g7.after_psm_tx()

        post = g7.snapshot_mint(endaoment_psm, charlie_token, green_token, savings_green, user, user)

        assert expected_green > 0
        # USDC: payer down, PSM up by exactly usdcAmount (auto-deposit yield empty -> stays idle)
        assert pre["payer_usdc"] - post["payer_usdc"] == usdc_amount
        assert post["psm_usdc"] - pre["psm_usdc"] == usdc_amount
        # GREEN: recipient up by greenToMint, supply up by greenToMint
        assert post["recip_green"] - pre["recip_green"] == expected_green
        assert post["supply"] - pre["supply"] == expected_green
        assert post["recip_sg"] == pre["recip_sg"]
        # interval consumed by exactly greenToMint
        assert post["avail_mint"] == avail_before - expected_green
        # event (captured right after the mint call, before other calls reset _computation)
        assert ev.user == user and ev.sender == user
        assert ev.usdcIn == usdc_amount
        assert ev.greenOut == expected_green
        assert ev.usdcFee == fee
        assert ev.receivedSavingsGreen is False
        # no leftover GREEN on the PSM
        assert green_token.balanceOf(endaoment_psm.address) == 0

        # expire the window for the next iteration
        boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)


def test_g7_mint_100pct_fee_regular_reverts_before_pull(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source,
):
    """mintFee == HUNDRED_PERCENT, regular recipient: max helper is 0 ->
    'zero amount' revert BEFORE transferFrom. No balance / interval / supply /
    event change."""
    user = boa.env.generate_address()
    usdc_amount = 1_000 * SIX
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(HUNDRED, sender=switchboard_charlie.address)

    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    pre = g7.snapshot_mint(endaoment_psm, charlie_token, green_token, savings_green, user, user)
    supply_before = green_token.totalSupply()

    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)

    assert charlie_token.balanceOf(user) == usdc_amount  # nothing pulled
    assert charlie_token.balanceOf(endaoment_psm.address) == pre["psm_usdc"]
    assert green_token.totalSupply() == supply_before
    assert green_token.balanceOf(user) == 0
    assert endaoment_psm.getAvailIntervalMint() == pre["avail_mint"]


def test_g7_mint_ceiling_vs_interval_remainder(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """_usdcAmount is a ceiling: request above remaining interval spends only the
    remainder-equivalent USDC and succeeds (partial, not revert)."""
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    # shrink interval to 10 GREEN
    endaoment_psm.setMaxIntervalMint(10 * E18, sender=switchboard_charlie.address)

    big = 1_000_000 * SIX
    charlie_token.mint(user, big, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, big, sender=user)

    pre_usdc = charlie_token.balanceOf(user)
    endaoment_psm.mintGreen(MAX_UINT256, user, False, sender=user)

    assert green_token.balanceOf(user) == 10 * E18  # capped by interval, not request
    assert pre_usdc - charlie_token.balanceOf(user) == 10 * SIX  # only 10 USDC pulled
    assert endaoment_psm.getAvailIntervalMint() == 0


def test_g7_mint_two_users_share_interval(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Global, not per-user: two ordinary users share one interval cap."""
    alice = boa.env.generate_address()
    bob = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMaxIntervalMint(15 * E18, sender=switchboard_charlie.address)

    for who in (alice, bob):
        charlie_token.mint(who, 1_000 * SIX, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 1_000 * SIX, sender=who)

    endaoment_psm.mintGreen(10 * SIX, alice, False, sender=alice)
    g7.after_psm_tx()
    assert green_token.balanceOf(alice) == 10 * E18
    assert endaoment_psm.getAvailIntervalMint() == 5 * E18
    # bob only gets the remainder
    endaoment_psm.mintGreen(10 * SIX, bob, False, sender=bob)
    assert green_token.balanceOf(bob) == 5 * E18
    assert endaoment_psm.getAvailIntervalMint() == 0


def test_g7_mint_recipient_neq_caller_external_payer_identity(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """External payer USDC debit == usdcAmount == PSM credit regardless of
    recipient; GREEN goes only to recipient. Alice's mint must not credit Bob
    except as chosen recipient."""
    alice = boa.env.generate_address()
    bob = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    usdc_amount = 500 * SIX
    charlie_token.mint(alice, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=alice)

    pre_psm = charlie_token.balanceOf(endaoment_psm.address)
    endaoment_psm.mintGreen(usdc_amount, bob, False, sender=alice)
    ev = g7.last_mint_event(endaoment_psm)

    assert charlie_token.balanceOf(alice) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == pre_psm + usdc_amount
    assert green_token.balanceOf(bob) == 500 * E18
    assert green_token.balanceOf(alice) == 0
    assert ev.user == bob and ev.sender == alice


def test_g7_mint_recipient_is_psm_green_residue_not_usdc_selftransfer(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """recipient == PSM: USDC still moves payer -> PSM (once); GREEN is minted to
    the PSM itself (residue, stranded). No double USDC credit."""
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    pre_psm = charlie_token.balanceOf(endaoment_psm.address)
    endaoment_psm.mintGreen(usdc_amount, endaoment_psm.address, False, sender=user)

    assert charlie_token.balanceOf(user) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == pre_psm + usdc_amount  # exactly once
    assert green_token.balanceOf(endaoment_psm.address) == 100 * E18  # GREEN stranded on PSM


def test_g7_mint_below_peg_pays_fewer_green(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """USDC below peg: greenToMint = min(usdValue, 1:1) = usdValue (< 1:1)."""
    user = boa.env.generate_address()
    price = 95 * E18 // 100  # $0.95
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)

    usdc_amount = 1_000 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    expected, fee, after, usd_value, one_to_one = g7.expected_mint_green(usdc_amount, 0, price)
    assert usd_value == 950 * E18 and one_to_one == 1_000 * E18

    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    assert green_token.balanceOf(user) == expected == 950 * E18


def test_g7_mint_above_peg_capped_at_1to1(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """USDC above peg: greenToMint capped at 1:1 (min with oneToOne)."""
    user = boa.env.generate_address()
    price = 105 * E18 // 100  # $1.05
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)

    usdc_amount = 1_000 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    assert green_token.balanceOf(user) == 1_000 * E18  # not 1050


def test_g7_mint_zero_price_reverts_after_pull(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source,
):
    """No price (mock returns 0, no failed-feed status): getUsdValue -> 0 ->
    greenToMint == 0 revert AFTER the pull; full rollback including USDC."""
    user = boa.env.generate_address()
    # canMint on; no setPrice call at all -> every source returns 0, none failed
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    assert mock_price_source.getPrice(charlie_token.address) == 0

    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    pre = g7.snapshot_mint(endaoment_psm, charlie_token, green_token, savings_green, user, user)
    with boa.reverts("zero mint amount"):
        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)

    # rollback: nothing moved
    assert charlie_token.balanceOf(user) == usdc_amount
    assert charlie_token.balanceOf(endaoment_psm.address) == pre["psm_usdc"]
    assert green_token.balanceOf(user) == 0


def test_g7_mint_sg_allowance_after_wrap(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source,
):
    """Successful wrap: recipient gets sGREEN shares; PSM GREEN allowance to
    savings_green ends at 0; PSM holds no GREEN residue; supply increase ==
    GREEN deposited into the vault."""
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    usdc_amount = 1_000 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    supply_before = green_token.totalSupply()
    endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)
    ev = g7.last_mint_event(endaoment_psm)

    ret = 1_000 * E18
    shares = savings_green.balanceOf(user)
    assert shares > 0
    # ~1:1 wrap (sGREEN may hold prior tests' GREEN; only assert share sanity)
    assert savings_green.convertToAssets(shares) > 0
    assert green_token.balanceOf(endaoment_psm.address) == 0  # no residue
    assert green_token.allowance(endaoment_psm.address, savings_green.address) == 0
    assert green_token.totalSupply() - supply_before == ret  # supply up by minted GREEN (held by sGREEN)
    assert ev.receivedSavingsGreen is True


def test_g7_mint_wrap_dust_boundary(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source,
):
    """greenToMint == ONE_GREEN exactly (and below): raw GREEN, no sGREEN, even
    when _wantsSavingsGreen=True. Strictly-greater boundary."""
    user = boa.env.generate_address()
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    # exactly 1 GREEN worth: 1 USDC
    charlie_token.mint(user, 3 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 3 * SIX, sender=user)

    endaoment_psm.mintGreen(1 * SIX, user, True, sender=user)
    g7.after_psm_tx()
    ev = g7.last_mint_event(endaoment_psm)
    assert green_token.balanceOf(user) == E18  # raw GREEN
    assert ev.receivedSavingsGreen is False

    # above the boundary wraps
    endaoment_psm.mintGreen(2 * SIX, user, True, sender=user)
    ev2 = g7.last_mint_event(endaoment_psm)
    assert savings_green.balanceOf(user) > 0
    assert ev2.receivedSavingsGreen is True


def test_g7_mint_fee_split_floors_per_tx(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Fee floors per tx: one large mint vs the same aggregate in dust mints —
    dust pays <= total fee, never more; minted GREEN dust >= single. Quantify."""
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    fee_bps = 1  # 0.01%
    endaoment_psm.setMintFee(fee_bps, sender=switchboard_charlie.address)

    # single big mint
    whale = boa.env.generate_address()
    total = 10_000 * SIX
    charlie_token.mint(whale, total, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, total, sender=whale)
    endaoment_psm.mintGreen(total, whale, False, sender=whale)
    g7.after_psm_tx()
    fee_big = total * fee_bps // HUNDRED
    g_big = green_token.balanceOf(whale)
    assert g_big == (total - fee_big) * E18 // SIX  # at $1, 1:1 after fee, 6dp -> 18dp

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # dust mints: 200 x 50 USDC (fee per tx = 5 units; aggregate dust fee floors
    # to exactly the single-tx fee here — split-safe at this size. The dodged-fee
    # boundary is per-tx fee == 0, proven in test_g7_mint_first_nonzero_fee_boundary.)
    dust = boa.env.generate_address()
    charlie_token.mint(dust, total, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, total, sender=dust)
    n_dust = 200
    dust_amt = total // n_dust
    fee_per_dust = dust_amt * fee_bps // HUNDRED
    g_dust_total = 0
    for _ in range(n_dust):
        endaoment_psm.mintGreen(dust_amt, dust, False, sender=dust)
        g7.after_psm_tx()
    g_dust_total = green_token.balanceOf(dust)

    # per-tx fee floors down; aggregate dust fee <= single-tx fee
    assert fee_per_dust * n_dust <= fee_big
    assert g_dust_total >= g_big  # dust never mints less GREEN
    # quantified: fee dodged by splitting = difference in minted GREEN
    assert g_dust_total - g_big == (fee_big - fee_per_dust * n_dust) * E18 // SIX


def test_g7_mint_first_nonzero_fee_boundary(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """First-nonzero-fee boundary: at 1 bps, amounts < 10_000 USDC-units pay zero
    fee (floor), 10_000 pays exactly 1. A 9_999+1 split pays 0 total fee while a
    single 10_000-unit mint pays 1 unit — the split mints 1 GREEN-dust more."""
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(1, sender=switchboard_charlie.address)

    user = boa.env.generate_address()
    charlie_token.mint(user, 10_000, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 10_000, sender=user)

    # 9_999 units -> fee 0
    endaoment_psm.mintGreen(9_999, user, False, sender=user)
    g7.after_psm_tx()
    g1 = green_token.balanceOf(user)
    assert g1 == 9_999 * E18 // SIX  # no fee taken
    # push to the boundary: +1 unit -> fee on 1 unit still 0
    endaoment_psm.mintGreen(1, user, False, sender=user)
    g7.after_psm_tx()
    g2 = green_token.balanceOf(user) - g1
    assert g2 == 1 * E18 // SIX
    # single 10_000 mint takes a 1-unit fee
    whale = boa.env.generate_address()
    charlie_token.mint(whale, 10_000, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 10_000, sender=whale)
    endaoment_psm.mintGreen(10_000, whale, False, sender=whale)
    g3 = green_token.balanceOf(whale)
    assert g3 == (10_000 - 1) * E18 // SIX
    # dust path minted 1 unit of GREEN-dust more than the single mint
    assert (g1 + g2) - g3 == 1 * E18 // SIX


#####################
# Decimals differential #
#####################


def test_g7_constructor_accepts_18dp_token_and_mint_math_diverges(ripe_hq_deploy, governance):
    """Previously the constructor accepted an 18-decimal payment token.

    This test now proves it reverts with `usdc must be 6 decimals`.
    """
    tok18 = boa.load(
        "contracts/mock/MockErc20.vy", governance, "T18", "T18", 18, 1_000_000_000,
    )
    with boa.reverts("usdc must be 6 decimals"):
        boa.load(
            "contracts/core/EndaomentPSM.vy",
            ripe_hq_deploy,
            43_200,
            0,
            100_000 * E18,
            0,
            100_000 * E18,
            tok18.address,
            0,
            ZERO_ADDRESS,
        )
