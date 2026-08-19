"""Local helpers for Group 7 PSM proofs. Not a test module."""

import boa

from constants import ZERO_ADDRESS
from conf_utils import clear_transient_storage, filter_logs


SIX = 10**6
E18 = 10**18
HUNDRED = 10_000
ONE_DAY_BLOCKS = 43_200
INTERVAL_GREEN = 100_000 * E18
MAX_UINT = 2**256 - 1


def after_psm_tx():
    """titanoboa 0.2.7: clear transient storage after a real PSM write.

    Call this after mintGreen / redeemGreen / depositToYield / withdrawFromYield
    when the test continues with another PSM write, including after a revert.
    """
    clear_transient_storage()


def _set_if(contract, getter, setter, value, sender):
    current = getter()
    if current != value:
        setter(value, sender=sender)


def reset_psm_regular(
    endaoment_psm,
    switchboard_charlie,
    mission_control,
    switchboard_alpha,
    mock_undy_v2=None,
):
    """Return the session-scoped PSM to a launch-shaped regular path.

    Expires the current interval window, clears fees / allowlists / yield,
    and clears MissionControl.underscoreRegistry. Restores MockUndyV2 defaults
    when the mock is passed.
    """
    duration = endaoment_psm.numBlocksPerInterval()
    if 0 < duration < 10_000_000:
        boa.env.time_travel(blocks=duration + 1)

    if endaoment_psm.isPaused():
        endaoment_psm.pause(False, sender=switchboard_charlie.address)

    _set_if(endaoment_psm, endaoment_psm.canMint, endaoment_psm.setCanMint, False, switchboard_charlie.address)
    _set_if(endaoment_psm, endaoment_psm.canRedeem, endaoment_psm.setCanRedeem, False, switchboard_charlie.address)
    _set_if(endaoment_psm, endaoment_psm.mintFee, endaoment_psm.setMintFee, 0, switchboard_charlie.address)
    _set_if(endaoment_psm, endaoment_psm.redeemFee, endaoment_psm.setRedeemFee, 0, switchboard_charlie.address)
    _set_if(
        endaoment_psm,
        endaoment_psm.shouldEnforceMintAllowlist,
        endaoment_psm.setShouldEnforceMintAllowlist,
        False,
        switchboard_charlie.address,
    )
    _set_if(
        endaoment_psm,
        endaoment_psm.shouldEnforceRedeemAllowlist,
        endaoment_psm.setShouldEnforceRedeemAllowlist,
        False,
        switchboard_charlie.address,
    )
    _set_if(
        endaoment_psm,
        endaoment_psm.maxIntervalMint,
        endaoment_psm.setMaxIntervalMint,
        INTERVAL_GREEN,
        switchboard_charlie.address,
    )
    _set_if(
        endaoment_psm,
        endaoment_psm.maxIntervalRedeem,
        endaoment_psm.setMaxIntervalRedeem,
        INTERVAL_GREEN,
        switchboard_charlie.address,
    )
    if endaoment_psm.numBlocksPerInterval() != ONE_DAY_BLOCKS:
        endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS, sender=switchboard_charlie.address)
        boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    if not endaoment_psm.shouldAutoDeposit():
        endaoment_psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)

    pos = endaoment_psm.usdcYieldPosition()
    if pos.legoId != 0 or pos.vaultToken != ZERO_ADDRESS:
        endaoment_psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)

    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)

    if mock_undy_v2 is not None:
        mock_undy_v2.setAllAddressesAreVaults(True)
        mock_undy_v2.setVaultCheckRevertAddress(ZERO_ADDRESS)
        mock_undy_v2.setMissingRegId(MAX_UINT)
        mock_undy_v2.setIsUserWallet(False)


def enable_mint(endaoment_psm, switchboard_charlie):
    if not endaoment_psm.canMint():
        endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)


def enable_redeem(endaoment_psm, switchboard_charlie):
    if not endaoment_psm.canRedeem():
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


def set_usdc_price(mock_price_source, charlie_token, price_e18):
    mock_price_source.setPrice(charlie_token.address, price_e18)


def fund_usdc(charlie_token, who, amount, governance):
    charlie_token.mint(who, amount, sender=governance.address)


def expected_mint_green(usdc_amount, fee_bps, price_e18):
    """Independent mint identity. PriceDesk forced-1 when price * after < 1e6."""
    fee = usdc_amount * fee_bps // HUNDRED
    after = usdc_amount - fee
    if after == 0 or price_e18 == 0:
        return 0, fee, after, 0, after * E18 // SIX
    numerator = price_e18 * after
    usd_value = 1 if numerator < SIX else numerator // SIX
    one_to_one = after * E18 // SIX
    return min(usd_value, one_to_one), fee, after, usd_value, one_to_one


def expected_redeem_usdc(green_amount, fee_bps, price_e18, vault):
    """Independent redeem identity (honest 6-dec USDC).
    priceDesk leg = getAssetAmount = greenAmount(18dp USD) * 1e6 // price."""
    if green_amount == 0 or price_e18 == 0:
        return 0, 0, 0, 0, 0
    from_desk = green_amount * SIX // price_e18
    one_to_one = green_amount * SIX // E18
    usdc_to_give = max(from_desk, one_to_one) if vault else min(from_desk, one_to_one)
    fee = 0 if vault else usdc_to_give * fee_bps // HUNDRED
    return usdc_to_give - fee, fee, usdc_to_give, from_desk, one_to_one


def last_mint_event(endaoment_psm):
    logs = filter_logs(endaoment_psm, "MintGreen")  # last-call logs; strict would raise when absent
    assert logs, "missing MintGreen"
    return logs[-1]


def last_redeem_event(endaoment_psm):
    logs = filter_logs(endaoment_psm, "RedeemGreen")
    assert logs, "missing RedeemGreen"
    return logs[-1]


def snapshot_mint(endaoment_psm, charlie_token, green_token, savings_green, payer, recipient):
    return {
        "payer_usdc": charlie_token.balanceOf(payer),
        "psm_usdc": charlie_token.balanceOf(endaoment_psm.address),
        "recip_green": green_token.balanceOf(recipient),
        "payer_green": green_token.balanceOf(payer),
        "recip_sg": savings_green.balanceOf(recipient),
        "supply": green_token.totalSupply(),
        "avail_mint": endaoment_psm.getAvailIntervalMint(),
        "interval": endaoment_psm.globalMintInterval(),
        "yield_underlying": endaoment_psm.getUnderlyingYieldAmount(),
    }


def snapshot_redeem(endaoment_psm, charlie_token, green_token, savings_green, payer, recipient):
    return {
        "payer_green": green_token.balanceOf(payer),
        "payer_sg": savings_green.balanceOf(payer),
        "recip_usdc": charlie_token.balanceOf(recipient),
        "psm_usdc": charlie_token.balanceOf(endaoment_psm.address),
        "supply": green_token.totalSupply(),
        "avail_redeem": endaoment_psm.getAvailIntervalRedemptions(),
        "interval": endaoment_psm.globalRedeemInterval(),
        "yield_underlying": endaoment_psm.getUnderlyingYieldAmount(),
        "psm_green": green_token.balanceOf(endaoment_psm.address),
    }
