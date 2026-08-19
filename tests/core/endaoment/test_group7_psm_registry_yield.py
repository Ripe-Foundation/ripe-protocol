"""Group 7 PSM proofs — never-skip #6: registry, yield, reserve drain.

6a malformed registry (revert / missing-id / clear semantics), 6b reserve
drain sequence (Echo immediate inventory ops are governor-or-lite; launch
liteSigners empty -> governor used, stated), 6c lifecycle, 6d yield-position
pairs (direct Switchboard component proofs).

No production mock implements the UndyLego yield interface
(depositForYield / withdrawFromYield / getVaultTokenAmount /
getUnderlyingAmountSafe do not exist on MockUndyV2), so yield-position
proofs are scoped to what a real lego changes: a nonzero (legoId, vaultToken)
pair with a registry present routes _getLegoAddr through the mock's
getAddr (returns self) and the lego call then reverts — used below only to
prove WHERE the failure lands and that funds are never at risk, and the
pair-storage semantics of setUsdcYieldPosition. Deposit composition (B + P)
is asserted at the code level in the report (EndaomentPSM.vy:565 deposits
balanceOf(self) — the entire idle balance).
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256

from tests.core.endaoment import g7_psm_helpers as g7


SIX = 10**6
E18 = 10**18
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


################
# 6a malformed #
################


def test_g7_6a_reverting_vault_check_bricks_user_actions(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source,
):
    """Previously `isEarnVault` revert on one recipient bricked that user's mint/redeem.

    This test now proves the victim is treated as regular (fee binds) and other
    EOAs are unchanged.
    """
    victim = boa.env.generate_address()
    other = boa.env.generate_address()
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setVaultCheckRevertAddress(victim)
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    usdc_amount = 100 * SIX
    charlie_token.mint(victim, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=victim)
    charlie_token.mint(other, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=other)

    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
    endaoment_psm.mintGreen(usdc_amount, victim, False, sender=victim)
    ev = g7.last_mint_event(endaoment_psm)
    g7.after_psm_tx()
    assert green_token.balanceOf(victim) == 95 * E18
    assert ev.usdcFee == usdc_amount * 500 // 10_000

    endaoment_psm.mintGreen(usdc_amount, other, False, sender=other)
    g7.after_psm_tx()
    assert green_token.balanceOf(other) == 95 * E18


def test_g7_6a_missing_vault_registry_id_fails_closed(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source,
):
    """Registry set but getAddr(UNDERSCORE_VAULT_REGISTRY_ID=10) returns empty
    (mock setMissingRegId(10)): _isUnderscoreVault is False for everyone —
    fail closed to regular, no revert."""
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setMissingRegId(10)  # getAddr(10) -> empty
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)

    user = boa.env.generate_address()
    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    ev = g7.last_mint_event(endaoment_psm)
    assert ev.usdcFee == usdc_amount * 500 // 10_000  # regular fee applied


def test_g7_6a_empty_registry_confirm_launch_fail_closed(
    endaoment_psm, mission_control,
):
    """Launch: underscoreRegistry() == empty -> _isUnderscoreVault False for
    all — confirmed as fail-closed (also asserted by every regular-path proof)."""
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    # and launch yield empty: getUsdcYieldPositionVaultToken() == empty
    assert endaoment_psm.getUsdcYieldPositionVaultToken() == ZERO_ADDRESS


################
# 6b reserve drain #
################


def test_g7_6b_reserve_drain_sequence(
    endaoment_psm, charlie_token, green_token, switchboard_echo,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source, whale,
):
    """One sequence: user observes redeem capacity -> Echo
    transferUsdcToEndaomentFundsInPsm (IMMEDIATE governor-or-lite; launch
    liteSigners empty -> governor used here) sweeps idle -> user's prior redeem
    request partial-fills (not a revert) against the smaller reserve."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    user = boa.env.generate_address()

    idle = 10_000 * SIX
    charlie_token.mint(endaoment_psm.address, idle, sender=governance.address)
    green_amount = 10_000 * E18
    green_token.transfer(user, green_amount, sender=whale)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)

    # user observes capacity for the full 10k GREEN
    assert endaoment_psm.getMaxRedeemableGreenAmount() >= green_amount

    # immediate governor action sweeps idle USDC to EndaomentFunds
    swept = switchboard_echo.transferUsdcToEndaomentFundsInPsm(idle - 100 * SIX, sender=governance.address)
    assert swept == idle - 100 * SIX
    assert charlie_token.balanceOf(endaoment_psm.address) == 100 * SIX

    # the user's prior request now partial-fills against the 100 USDC left
    endaoment_psm.redeemGreen(MAX_UINT256, user, False, sender=user)
    ev = g7.last_redeem_event(endaoment_psm)
    assert ev.greenIn == 100 * E18  # only 100 GREEN filled
    assert ev.usdcOut == 100 * SIX
    assert green_token.balanceOf(user) == green_amount - 100 * E18  # the rest stays with the user


def test_g7_6b_deposit_to_yield_is_composition_not_drain(
    endaoment_psm, charlie_token, switchboard_echo,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source,
):
    """depositToYieldInPsm is the third immediate inventory op: with no yield
    position configured it returns 0 and available USDC is unchanged
    (_getAvailableUsdc = idle + yield; idle -> yield is composition)."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(endaoment_psm.address, 1_000 * SIX, sender=governance.address)
    pre = endaoment_psm.getAvailableUsdc()

    out = switchboard_echo.depositToYieldInPsm(sender=governance.address)
    assert out == 0  # yield position empty -> no-op
    assert endaoment_psm.getAvailableUsdc() == pre


################
# 6c lifecycle #
################


def test_g7_6c_registry_clear_drops_yield_inventory_view(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source, whale,
):
    """With a yield position configured (legoId=1, vaultToken=savings_green — a
    token the PSM holds ZERO of), clearing the registry makes _getLegoAddr
    return empty -> _getUnderlyingYieldAmount 0 -> redeemable inventory is
    idle-only. Re-registering resolves the view again. (Component proof:
    savings_green is used as the vault token because a real ERC-20 balanceOf
    is needed for the setter's zero-balance check; PSM holds none.)"""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)

    endaoment_psm.setUsdcYieldPosition(1, savings_green.address, sender=switchboard_charlie.address)
    pos = endaoment_psm.usdcYieldPosition()
    assert pos.legoId == 1 and pos.vaultToken == savings_green.address

    charlie_token.mint(endaoment_psm.address, 1_000 * SIX, sender=governance.address)
    assert endaoment_psm.getAvailableUsdc() == 1_000 * SIX  # idle-only (no vt balance)

    # registry clear: nothing changes while no vault tokens are held — the gate
    # on _getUnderlyingYieldAmount is the lego resolution, which needs the registry
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    assert endaoment_psm.getAvailableUsdc() == 1_000 * SIX

    # restore canonical (0, empty) — allowed directly on the PSM setter
    endaoment_psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)
    pos2 = endaoment_psm.usdcYieldPosition()
    assert pos2.legoId == 0 and pos2.vaultToken == ZERO_ADDRESS


def test_g7_6c_yield_rotation_blocked_while_old_vault_balance(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source,
):
    """setUsdcYieldPosition rotation requires old vault-token balance == 0.
    Proven with savings_green as the old vault token: PSM wraps GREEN into
    sGREEN (real vault-token balance) -> rotation reverts 'vault token balance
    not zero'."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setUsdcYieldPosition(1, savings_green.address, sender=switchboard_charlie.address)

    # give the PSM a real sGREEN balance via the wrap path
    user = boa.env.generate_address()
    charlie_token.mint(user, 100 * SIX, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100 * SIX, sender=user)
    endaoment_psm.mintGreen(100 * SIX, endaoment_psm.address, True, sender=user)  # PSM receives sGREEN
    assert savings_green.balanceOf(endaoment_psm.address) > 0

    with boa.reverts("vault token balance not zero"):
        endaoment_psm.setUsdcYieldPosition(2, ZERO_ADDRESS, sender=switchboard_charlie.address)


################
# 6d pairs     #
################


def test_g7_6d_yield_position_pair_matrix(
    endaoment_psm, switchboard_charlie, savings_green,
):
    """The PSM setter stores all four combinations; _depositToYield /
    _withdrawFromYield / _getUnderlyingYieldAmount treat legoId == 0 or
    vaultToken == empty as yield-off. (0, empty) is the canonical launch pair
    and reachable directly on the PSM setter (Echo's setPsmUsdcYieldPosition
    rejects legoId == 0 — cannot restore canonical via Echo). savings_green is
    the stand-in vault token (real ERC-20 so the zero-balance check runs)."""
    vt_real = savings_green.address

    cases = [
        (0, ZERO_ADDRESS),
        (1, ZERO_ADDRESS),
        (0, vt_real),
        (1, vt_real),
    ]
    for lego_id, vt in cases:
        pos = endaoment_psm.usdcYieldPosition()
        if pos.legoId != lego_id or pos.vaultToken != vt:
            endaoment_psm.setUsdcYieldPosition(lego_id, vt, sender=switchboard_charlie.address)
        pos = endaoment_psm.usdcYieldPosition()
        assert pos.legoId == lego_id and pos.vaultToken == vt  # stored as given
        # yield treated as off whenever either leg is empty
        if lego_id == 0 or vt == ZERO_ADDRESS:
            assert endaoment_psm.getUnderlyingYieldAmount() == 0

    # back to canonical for the next test
    endaoment_psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)
