"""Group 7 (PSM) — never-skip #1: mint conservation.

USDC (6dp, ``charlie_token`` locally) -> GREEN / sGREEN through
``EndaomentPSM.mintGreen``.  Every expected value here is re-derived from
``contracts/core/EndaomentPSM.vy`` arithmetic, not copied from an existing
test.

Units (do not mix):
  * USDC in / fee / idle          -> 6 decimals
  * GREEN minted / interval amount-> 18 decimals
  * sGREEN out                    -> shares
  * fees                          -> bps against HUNDRED_PERCENT = 100_00
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


SIX_DECIMALS = 10**6
ONE_USDC = 10**6
ONE_GREEN = 10**18
HUNDRED_PERCENT = 100_00


# ---------------------------------------------------------------- helpers


def _expected_green(usdc_after_fee, price):
    """Re-derivation of the PSM mint formula.

    PriceDesk.getUsdValue(usdc, amt) == price * amt // 10**6  (USDC is 6dp),
    forced to 1 when a positive numerator would floor to zero.
    PSM then takes min(usdValue, amt * ONE_GREEN // ONE_USDC).
    """
    numerator = price * usdc_after_fee
    if usdc_after_fee == 0 or price == 0:
        usd_value = 0
    elif numerator < ONE_USDC:
        usd_value = 1
    else:
        usd_value = numerator // ONE_USDC
    one_to_one = usdc_after_fee * ONE_GREEN // ONE_USDC
    return min(usd_value, one_to_one)


def _enable_mint(psm, switchboard_charlie):
    if not psm.canMint():
        psm.setCanMint(True, sender=switchboard_charlie.address)


def _set_mint_fee(psm, switchboard_charlie, fee):
    if psm.mintFee() != fee:
        psm.setMintFee(fee, sender=switchboard_charlie.address)


def _fund(charlie_token, governance, who, amount, psm):
    charlie_token.mint(who, amount, sender=governance.address)
    charlie_token.approve(psm.address, amount, sender=who)


# ---------------------------------------------------------------- 1. base


def test_g7_mint_conservation_full_ledger_at_peg(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """Every measured quantity on a plain at-peg mint, independently derived."""
    psm = endaoment_psm
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(charlie_token.address, price)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    _fund(charlie_token, governance, user, usdc_amount, psm)

    pre_payer = charlie_token.balanceOf(user)
    pre_psm_usdc = charlie_token.balanceOf(psm.address)
    pre_supply = green_token.totalSupply()
    pre_user_green = green_token.balanceOf(user)
    pre_interval = psm.globalMintInterval()

    ret = psm.mintGreen(usdc_amount, user, False, sender=user)
    log = filter_logs(psm, "MintGreen")[0]

    exp_green = _expected_green(usdc_amount, price)
    assert exp_green == 1000 * EIGHTEEN_DECIMALS

    # payer USDC debit == usdcAmount == PSM USDC credit (yield off, so idle)
    assert pre_payer - charlie_token.balanceOf(user) == usdc_amount
    assert charlie_token.balanceOf(psm.address) - pre_psm_usdc == usdc_amount
    # GREEN supply increase == recipient GREEN increase == greenToMint
    assert green_token.totalSupply() - pre_supply == exp_green
    assert green_token.balanceOf(user) - pre_user_green == exp_green
    assert ret == exp_green
    # interval consumed exactly greenToMint (GREEN units)
    post_interval = psm.globalMintInterval()
    assert post_interval.amount - (pre_interval.amount if pre_interval.start != 0 else 0) >= 0
    assert post_interval.start == boa.env.evm.patch.block_number
    assert post_interval.amount == exp_green
    # no residue on the PSM
    assert green_token.balanceOf(psm.address) == 0

    assert log.user == user
    assert log.sender == user
    assert log.usdcIn == usdc_amount
    assert log.greenOut == exp_green
    assert log.usdcFee == 0
    assert log.receivedSavingsGreen is False


@pytest.mark.parametrize("price_num", [95, 100, 105])
def test_g7_mint_peg_grid_regular(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, price_num
):
    """min(usdValue, 1:1) holds below / at / above peg."""
    psm = endaoment_psm
    price = price_num * EIGHTEEN_DECIMALS // 100
    mock_price_source.setPrice(charlie_token.address, price)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    _fund(charlie_token, governance, user, usdc_amount, psm)

    pre_supply = green_token.totalSupply()
    ret = psm.mintGreen(usdc_amount, user, False, sender=user)

    exp = _expected_green(usdc_amount, price)
    assert ret == exp
    assert green_token.totalSupply() - pre_supply == exp
    assert green_token.balanceOf(user) == exp
    # above peg the 1:1 leg binds; below peg the oracle leg binds
    if price_num >= 100:
        assert exp == usdc_amount * ONE_GREEN // ONE_USDC
    else:
        assert exp == price * usdc_amount // ONE_USDC
        assert exp < usdc_amount * ONE_GREEN // ONE_USDC


@pytest.mark.parametrize("fee", [0, 1, 5_00, 9_999])
def test_g7_mint_fee_grid_regular(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, fee
):
    """fee = usdcAmount * feeBps // 10_000 (floor); fee USDC stays on the PSM."""
    psm = endaoment_psm
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(charlie_token.address, price)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, fee)

    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    _fund(charlie_token, governance, user, usdc_amount, psm)

    pre_psm_usdc = charlie_token.balanceOf(psm.address)
    pre_supply = green_token.totalSupply()
    ret = psm.mintGreen(usdc_amount, user, False, sender=user)

    exp_fee = usdc_amount * fee // HUNDRED_PERCENT
    exp_after_fee = usdc_amount - exp_fee
    exp_green = _expected_green(exp_after_fee, price)

    assert ret == exp_green
    assert green_token.totalSupply() - pre_supply == exp_green
    # the PSM keeps the whole payment (fee is not a separate bucket)
    assert charlie_token.balanceOf(psm.address) - pre_psm_usdc == usdc_amount
    log = filter_logs(psm, "MintGreen")[0]
    assert log.usdcFee == exp_fee
    assert log.usdcIn == usdc_amount


def test_g7_mint_hundred_percent_fee_regular_reverts_before_pull(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """mintFee == HUNDRED_PERCENT -> max helper 0 -> zero-amount revert before transferFrom."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, HUNDRED_PERCENT)

    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    _fund(charlie_token, governance, user, usdc_amount, psm)

    assert psm.getMaxUsdcAmountForMint(user, False) == 0
    pre_payer = charlie_token.balanceOf(user)
    pre_psm = charlie_token.balanceOf(psm.address)
    pre_supply = green_token.totalSupply()
    pre_allowance = charlie_token.allowance(user, psm.address)
    pre_interval = psm.globalMintInterval()

    with boa.reverts("zero amount"):
        psm.mintGreen(usdc_amount, user, False, sender=user)

    assert charlie_token.balanceOf(user) == pre_payer
    assert charlie_token.balanceOf(psm.address) == pre_psm
    assert green_token.totalSupply() == pre_supply
    assert charlie_token.allowance(user, psm.address) == pre_allowance
    assert psm.globalMintInterval() == pre_interval


# ---------------------------------------------------------------- recipients


def test_g7_mint_external_payer_usdc_flow_is_recipient_independent(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """USDC always moves payer -> PSM; _recipient only steers GREEN."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    payer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    bystander = boa.env.generate_address()
    usdc_amount = 500 * SIX_DECIMALS
    _fund(charlie_token, governance, payer, usdc_amount, psm)

    pre_psm = charlie_token.balanceOf(psm.address)
    ret = psm.mintGreen(usdc_amount, recipient, False, sender=payer)

    assert charlie_token.balanceOf(payer) == 0
    assert charlie_token.balanceOf(psm.address) - pre_psm == usdc_amount
    assert charlie_token.balanceOf(recipient) == 0  # recipient pays nothing
    assert green_token.balanceOf(recipient) == ret
    assert green_token.balanceOf(payer) == 0
    assert green_token.balanceOf(bystander) == 0  # no cross-user credit

    log = filter_logs(psm, "MintGreen")[0]
    assert log.user == recipient
    assert log.sender == payer


def test_g7_mint_recipient_is_psm_leaves_green_residue_not_usdc_selftransfer(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """recipient == PSM: GREEN residue accrues on the PSM; USDC still moves in normally."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    payer = boa.env.generate_address()
    usdc_amount = 250 * SIX_DECIMALS
    _fund(charlie_token, governance, payer, usdc_amount, psm)

    pre_psm_usdc = charlie_token.balanceOf(psm.address)
    pre_psm_green = green_token.balanceOf(psm.address)
    pre_supply = green_token.totalSupply()

    ret = psm.mintGreen(usdc_amount, psm.address, False, sender=payer)

    assert charlie_token.balanceOf(payer) == 0
    assert charlie_token.balanceOf(psm.address) - pre_psm_usdc == usdc_amount
    # GREEN is stranded on the PSM: supply rose but nobody can claim it
    assert green_token.balanceOf(psm.address) - pre_psm_green == ret
    assert green_token.totalSupply() - pre_supply == ret


# ---------------------------------------------------------------- ceilings


def test_g7_mint_amount_argument_is_a_ceiling_not_an_exact_fill(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """Requesting more than the remaining interval spends less and still succeeds."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    max_interval = psm.maxIntervalMint()  # GREEN
    user = boa.env.generate_address()
    # fund well beyond the interval, in USDC units
    funding = (max_interval // 10**12) * 2
    _fund(charlie_token, governance, user, funding, psm)

    avail_before = psm.getAvailIntervalMint()
    quote = psm.getMaxUsdcAmountForMint(user, False)
    assert quote == avail_before * ONE_USDC // ONE_GREEN

    ret = psm.mintGreen(MAX_UINT256, user, False, sender=user)
    after_psm_tx()

    assert ret == avail_before  # filled to the cap, not to the argument
    assert charlie_token.balanceOf(user) == funding - quote
    assert psm.getAvailIntervalMint() == 0

    # a second mint in the same window is now blocked at the zero-amount assert
    with boa.reverts("zero amount"):
        psm.mintGreen(MAX_UINT256, user, False, sender=user)


def test_g7_mint_capped_by_payer_balance(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    user = boa.env.generate_address()
    bal = 37 * SIX_DECIMALS
    _fund(charlie_token, governance, user, bal, psm)

    assert psm.getMaxUsdcAmountForMint(user, False) == bal
    ret = psm.mintGreen(MAX_UINT256, user, False, sender=user)
    assert ret == _expected_green(bal, 1 * EIGHTEEN_DECIMALS)
    assert charlie_token.balanceOf(user) == 0


def test_g7_mint_two_users_share_one_global_interval(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    alice = boa.env.generate_address()
    bob = boa.env.generate_address()
    cap = psm.maxIntervalMint()
    half_usdc = (cap // 10**12) // 2
    _fund(charlie_token, governance, alice, half_usdc, psm)
    _fund(charlie_token, governance, bob, cap // 10**12, psm)

    a = psm.mintGreen(MAX_UINT256, alice, False, sender=alice)
    after_psm_tx()
    assert psm.getAvailIntervalMint() == cap - a

    b = psm.mintGreen(MAX_UINT256, bob, False, sender=bob)
    assert a + b == cap
    assert psm.getAvailIntervalMint() == 0
    assert psm.globalMintInterval().amount == cap
    # Bob was throttled by Alice's consumption, not by his own balance
    assert charlie_token.balanceOf(bob) > 0


# ---------------------------------------------------------------- sGREEN wrap


def test_g7_mint_savings_green_wrap_and_allowance_reset(
    endaoment_psm, charlie_token, green_token, savings_green, switchboard_charlie, governance, mock_price_source, whale
):
    """greenToMint > ONE_GREEN wraps; allowance ends at 0; sGREEN shares are the recipient credit."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    # give sGREEN a non-trivial share price so shares != assets
    green_token.approve(savings_green.address, 100 * EIGHTEEN_DECIMALS, sender=whale)
    savings_green.deposit(100 * EIGHTEEN_DECIMALS, whale, sender=whale)
    green_token.transfer(savings_green.address, 25 * EIGHTEEN_DECIMALS, sender=whale)

    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    _fund(charlie_token, governance, user, usdc_amount, psm)

    exp_green = _expected_green(usdc_amount, 1 * EIGHTEEN_DECIMALS)
    exp_shares = savings_green.convertToShares(exp_green)
    pre_supply = green_token.totalSupply()

    ret = psm.mintGreen(usdc_amount, user, True, sender=user)

    # return value is GREEN (18dp), recipient credit is sGREEN shares - different units
    assert ret == exp_green
    assert savings_green.balanceOf(user) == exp_shares
    assert green_token.balanceOf(user) == 0
    assert green_token.balanceOf(psm.address) == 0
    assert green_token.totalSupply() - pre_supply == exp_green
    assert green_token.allowance(psm.address, savings_green.address) == 0

    log = filter_logs(psm, "MintGreen")[0]
    assert log.receivedSavingsGreen is True
    assert log.greenOut == exp_green


def test_g7_mint_savings_green_dust_fallback_at_exactly_one_green(
    endaoment_psm, charlie_token, green_token, savings_green, switchboard_charlie, governance, mock_price_source
):
    """The wrap is strictly `> ONE_GREEN`; == ONE_GREEN falls back to raw GREEN."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 0)

    user = boa.env.generate_address()
    _fund(charlie_token, governance, user, 10 * SIX_DECIMALS, psm)

    # exactly 1 USDC -> exactly 1e18 GREEN -> NOT > ONE_GREEN
    ret = psm.mintGreen(1 * SIX_DECIMALS, user, True, sender=user)
    after_psm_tx()
    assert ret == ONE_GREEN
    assert green_token.balanceOf(user) == ONE_GREEN
    assert savings_green.balanceOf(user) == 0
    log = filter_logs(psm, "MintGreen")[0]
    assert log.receivedSavingsGreen is False

    # one micro-USDC more crosses the threshold and wraps
    ret2 = psm.mintGreen(1 * SIX_DECIMALS + 1, user, True, sender=user)
    assert ret2 > ONE_GREEN
    assert savings_green.balanceOf(user) > 0
    log2 = filter_logs(psm, "MintGreen")[0]
    assert log2.receivedSavingsGreen is True


# ---------------------------------------------------------------- fee splitting


def test_g7_mint_fee_floor_lets_dust_mints_avoid_the_fee(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """`fee = usdcAmount * bps // 10_000` floors per tx, so sub-threshold mints pay 0.

    Quantified, not pre-labelled: with a 1% fee the first non-zero fee lands at
    100 micro-USDC, so a payer splitting into 99-unit mints pays no fee at all.
    Gas makes this uneconomic at scale; the identity itself is what is proven.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable_mint(psm, switchboard_charlie)
    _set_mint_fee(psm, switchboard_charlie, 1_00)  # 1%

    # first non-zero fee boundary for 1%: amount * 100 // 10_000 >= 1  <=>  amount >= 100
    assert (99 * 1_00) // HUNDRED_PERCENT == 0
    assert (100 * 1_00) // HUNDRED_PERCENT == 1

    bulk_user = boa.env.generate_address()
    dust_user = boa.env.generate_address()
    total = 99 * 20  # 1980 micro-USDC, split into 20 x 99
    _fund(charlie_token, governance, bulk_user, total, psm)
    _fund(charlie_token, governance, dust_user, total, psm)

    bulk_green = psm.mintGreen(total, bulk_user, False, sender=bulk_user)
    after_psm_tx()
    bulk_fee = filter_logs(psm, "MintGreen")[0].usdcFee
    assert bulk_fee == total * 1_00 // HUNDRED_PERCENT == 19

    dust_green = 0
    dust_fee = 0
    for _ in range(20):
        dust_green += psm.mintGreen(99, dust_user, False, sender=dust_user)
        dust_fee += filter_logs(psm, "MintGreen")[0].usdcFee
        after_psm_tx()

    assert dust_fee == 0
    assert dust_green > bulk_green
    # both consumed the same USDC but the splitter minted more GREEN
    assert charlie_token.balanceOf(bulk_user) == charlie_token.balanceOf(dust_user) == 0
    # extra GREEN minted equals the evaded fee, converted 1:1
    assert dust_green - bulk_green == bulk_fee * ONE_GREEN // ONE_USDC
    # and it consumed more of the shared interval
    assert dust_green == total * ONE_GREEN // ONE_USDC


# ---------------------------------------------------------------- decimals


def test_g7_psm_payment_token_is_six_decimals(endaoment_psm, charlie_token):
    """Previously the constructor only checked nonzero USDC; it now requires 6 decimals."""
    assert charlie_token.decimals() == 6
    assert endaoment_psm.USDC() == charlie_token.address


def _load_psm(ripe_hq_deploy, usdc, name="g7_decimals_psm"):
    return boa.load(
        "contracts/core/EndaomentPSM.vy",
        ripe_hq_deploy,
        43_200,
        0,
        100_000 * EIGHTEEN_DECIMALS,
        0,
        100_000 * EIGHTEEN_DECIMALS,
        usdc,
        0,
        ZERO_ADDRESS,
        name=name,
    )


@pytest.mark.parametrize("token_fixture,decimals", [("alpha_token", 18), ("delta_token", 8)])
def test_g7_psm_constructor_rejects_wrong_decimal_payment_token(
    ripe_hq_deploy, request, token_fixture, decimals
):
    token = request.getfixturevalue(token_fixture)
    assert token.decimals() == decimals
    with boa.reverts("usdc must be 6 decimals"):
        _load_psm(ripe_hq_deploy, token, name="g7_wrong_decimals_psm")


def test_g7_constructor_rejects_token_whose_decimals_reverts(ripe_hq_deploy):
    reverting = boa.loads(
        """
# @version 0.4.3
@external
@view
def decimals() -> uint8:
    raise "no decimals"
""",
        name="g7_reverting_decimals",
    )
    with boa.reverts():
        _load_psm(ripe_hq_deploy, reverting.address, name="g7_reverting_decimals_psm")


def test_g7_constructor_rejects_address_with_no_decimals_abi(ripe_hq_deploy):
    with boa.reverts():
        _load_psm(
            ripe_hq_deploy,
            boa.env.generate_address(),
            name="g7_codeless_decimals_psm",
        )
