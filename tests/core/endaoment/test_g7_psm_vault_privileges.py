"""Group 7 (PSM) — never-skip #3: Underscore earn-vault recipient privileges.

Every test here pins the mock explicitly with ``setAllAddressesAreVaults(False)``
followed by ``setEarnVault(<addr>, True)``.  ``mock_undy_v2`` is session-scoped,
so the ``pinned_undy`` fixture restores the default afterwards.

The registry is installed with ``mission_control.setUnderscoreRegistry`` (fixture
setup for the vault *math*); never-skip #5 owns the production
``SwitchboardDelta.setUnderscoreRegistry`` install + clear.
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


@pytest.fixture
def pinned_undy(mission_control, mock_undy_v2, switchboard_alpha):
    """Registry installed + only explicitly-labelled addresses are earn vaults."""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    marked = []

    def mark(addr):
        mock_undy_v2.setEarnVault(addr, True)
        marked.append(addr)
        return addr

    yield mark

    for addr in marked:
        mock_undy_v2.setEarnVault(addr, False)
    mock_undy_v2.setAllAddressesAreVaults(True)


def _enable(psm, sb, mint=True, redeem=True):
    if mint and not psm.canMint():
        psm.setCanMint(True, sender=sb.address)
    if redeem and not psm.canRedeem():
        psm.setCanRedeem(True, sender=sb.address)


def _give_green(green_token, credit_engine, who, amount):
    """GREEN minted through a Ripe address that holds `canMintGreen` (CreditEngine).

    Stands in for credit-minted / secondary-market GREEN that the PSM did not
    itself create.  Not a CreditEngine borrow flow (Group 3 owns that).
    """
    green_token.mint(who, amount, sender=credit_engine.address)


# ------------------------------------------------------- keying: recipient only


def test_g7_vault_keying_is_recipient_not_sender(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    """caller-is-vault / recipient-is-EOA is REGULAR; caller-is-EOA / recipient-is-vault is VAULT."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 105 * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    vault = pinned_undy(boa.env.generate_address())
    eoa = boa.env.generate_address()
    green = 1_000 * EIGHTEEN_DECIMALS

    # sender IS the vault, recipient is an EOA -> conservative min()
    _give_green(green_token, credit_engine, vault, green)
    green_token.approve(psm.address, MAX_UINT256, sender=vault)
    got_regular = psm.redeemGreen(green, eoa, False, sender=vault)
    after_psm_tx()

    # sender is an EOA, recipient IS the vault -> favourable max()
    _give_green(green_token, credit_engine, eoa, green)
    green_token.approve(psm.address, MAX_UINT256, sender=eoa)
    got_vault = psm.redeemGreen(green, vault, False, sender=eoa)

    assert got_regular == 952380952           # 1000e18 * 1e6 // 1.05e18
    assert got_vault == 1_000 * SIX_DECIMALS  # the 1:1 leg wins the max()
    assert got_vault > got_regular


def test_g7_is_user_wallet_without_earn_vault_is_regular(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, mock_undy_v2, pinned_undy
):
    """`_isUnderscoreVault` calls `isEarnVault`, never `isUserWallet`."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 105 * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    wallet = boa.env.generate_address()
    mock_undy_v2.setUserWallet(wallet, True)
    assert mock_undy_v2.isUserWallet(wallet) is True
    assert mock_undy_v2.isEarnVault(wallet) is False

    user = boa.env.generate_address()
    green = 1_000 * EIGHTEEN_DECIMALS
    _give_green(green_token, credit_engine, user, green)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    got = psm.redeemGreen(green, wallet, False, sender=user)
    assert got == 952380952  # regular rate

    mock_undy_v2.setUserWallet(wallet, False)


def test_g7_empty_registry_is_regular_and_clearing_turns_skips_off(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, mission_control, mock_undy_v2, switchboard_alpha, pinned_undy
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 105 * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    green = 2_000 * EIGHTEEN_DECIMALS
    _give_green(green_token, credit_engine, user, green)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    with_registry = psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, vault, False, sender=user)
    after_psm_tx()
    assert with_registry == 1_000 * SIX_DECIMALS

    # clear the registry -> _isUnderscoreVault fails closed
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    after_clear = psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, vault, False, sender=user)
    assert after_clear == 952380952

    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)


def test_g7_psm_reads_only_underscore_registry_from_mission_control(endaoment_psm):
    """Source proof: the PSM's MissionControl interface has exactly one method.

    None of the seven Group 9 per-user bits (`setUndyLegoAccess` included) can
    reach the PSM's fee / allowlist / rate decisions.
    """
    import re
    from pathlib import Path

    src = Path("contracts/core/EndaomentPSM.vy").read_text()
    block = re.search(r"interface MissionControl:\n((?:    .*\n)+)", src).group(1)
    methods = re.findall(r"def (\w+)\(", block)
    assert methods == ["underscoreRegistry"]
    # and it is the only MissionControl call site shape in the file
    assert src.count("MissionControl(") == src.count("MissionControl(_missionControl).underscoreRegistry()") == 2


# ------------------------------------------------------- mint privileges


def test_g7_vault_mint_has_no_interval_cap_at_all(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, pinned_undy
):
    """`_calculateMaxUsdcForMint` returns max_value for a vault recipient.

    The PSM's only supply-rate control (maxIntervalMint, 100k GREEN) simply does
    not exist on this path, and the interval storage is never written.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    if psm.mintFee() != 0:
        psm.setMintFee(0, sender=switchboard_charlie.address)

    cap = psm.maxIntervalMint()
    assert cap == 100_000 * EIGHTEEN_DECIMALS

    vault = pinned_undy(boa.env.generate_address())
    payer = boa.env.generate_address()
    funding = 500_000 * SIX_DECIMALS  # 5x the interval cap
    charlie_token.mint(payer, funding, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=payer)

    assert psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, True) == MAX_UINT256
    pre_interval = psm.globalMintInterval()
    assert (pre_interval.start, pre_interval.amount) == (0, 0)

    minted = psm.mintGreen(MAX_UINT256, vault, False, sender=payer)

    assert minted == 500_000 * EIGHTEEN_DECIMALS   # 5x the global cap, one tx
    assert green_token.balanceOf(vault) == minted
    post = psm.globalMintInterval()
    assert (post.start, post.amount) == (0, 0)      # interval untouched
    assert psm.getAvailIntervalMint() == cap        # ordinary users unaffected


def test_g7_vault_mint_across_many_txs_leaves_global_interval_at_zero(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, pinned_undy
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    if psm.mintFee() != 0:
        psm.setMintFee(0, sender=switchboard_charlie.address)

    vault = pinned_undy(boa.env.generate_address())
    payer = boa.env.generate_address()
    charlie_token.mint(payer, 1_000_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=payer)

    total = 0
    for _ in range(10):
        total += psm.mintGreen(80_000 * SIX_DECIMALS, vault, False, sender=payer)
        after_psm_tx()

    assert total == 800_000 * EIGHTEEN_DECIMALS      # 8x the per-interval cap
    assert psm.globalMintInterval().amount == 0
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint()


def test_g7_vault_mint_skips_fee_even_at_one_hundred_percent(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, pinned_undy
):
    """A 100% mint fee blocks every ordinary user but not a vault recipient."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    psm.setMintFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)

    vault = pinned_undy(boa.env.generate_address())
    payer = boa.env.generate_address()
    charlie_token.mint(payer, 2_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=payer)

    # adjacent positive control: the same payer to an EOA recipient is dead
    assert psm.getMaxUsdcAmountForMint(payer, False) == 0
    with boa.reverts("zero amount"):
        psm.mintGreen(1_000 * SIX_DECIMALS, payer, False, sender=payer)
    after_psm_tx()

    minted = psm.mintGreen(1_000 * SIX_DECIMALS, vault, False, sender=payer)
    log = filter_logs(psm, "MintGreen")[0]
    assert minted == 1_000 * EIGHTEEN_DECIMALS
    assert log.usdcFee == 0

    psm.setMintFee(0, sender=switchboard_charlie.address)


def test_g7_vault_recipient_skips_mint_allowlist(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, pinned_undy
):
    """An unlisted sender mints freely by naming any registered earn vault."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    vault = pinned_undy(boa.env.generate_address())
    outsider = boa.env.generate_address()
    charlie_token.mint(outsider, 2_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=outsider)
    assert psm.mintAllowlist(outsider) is False

    with boa.reverts("not on mint allowlist"):
        psm.mintGreen(1_000 * SIX_DECIMALS, outsider, False, sender=outsider)
    after_psm_tx()

    minted = psm.mintGreen(1_000 * SIX_DECIMALS, vault, False, sender=outsider)
    assert minted == 1_000 * EIGHTEEN_DECIMALS

    psm.setShouldEnforceMintAllowlist(False, sender=switchboard_charlie.address)


def test_g7_vault_recipient_skips_redeem_allowlist(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)
    psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)

    vault = pinned_undy(boa.env.generate_address())
    outsider = boa.env.generate_address()
    _give_green(green_token, credit_engine, outsider, 2_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=outsider)

    with boa.reverts("not on redeem allowlist"):
        psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, outsider, False, sender=outsider)
    after_psm_tx()

    got = psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, vault, False, sender=outsider)
    assert got == 1_000 * SIX_DECIMALS

    psm.setShouldEnforceRedeemAllowlist(False, sender=switchboard_charlie.address)


# ------------------------------------------------------- redeem privileges


def test_g7_vault_redeem_drains_whole_reserve_in_one_tx_past_the_interval(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    """Ordinary redeemers sit behind maxIntervalRedeem; a vault recipient does not."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)

    reserve = 250_000 * SIX_DECIMALS               # 2.5x the 100k GREEN interval
    charlie_token.mint(psm.address, reserve, sender=governance.address)

    ordinary = boa.env.generate_address()
    _give_green(green_token, credit_engine, ordinary, 250_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=ordinary)
    assert psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False) == psm.maxIntervalRedeem()

    vault = pinned_undy(boa.env.generate_address())
    attacker = boa.env.generate_address()
    _give_green(green_token, credit_engine, attacker, 250_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=attacker)
    assert psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True) == 250_000 * EIGHTEEN_DECIMALS

    got = psm.redeemGreen(MAX_UINT256, vault, False, sender=attacker)
    after_psm_tx()
    assert got == reserve
    assert charlie_token.balanceOf(psm.address) == 0
    assert charlie_token.balanceOf(vault) == reserve
    assert psm.globalRedeemInterval().amount == 0   # interval never written

    # the ordinary redeemer, who was capped at 100k GREEN, now gets nothing
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, ordinary, False, sender=ordinary)


@pytest.mark.parametrize(
    "price_num,exp_vault,exp_regular",
    [
        (95, 1052631578, 1_000 * SIX_DECIMALS),
        (100, 1_000 * SIX_DECIMALS, 1_000 * SIX_DECIMALS),
        (105, 1_000 * SIX_DECIMALS, 952380952),
    ],
)
def test_g7_vault_max_vs_regular_min_same_green_burned(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy, price_num, exp_vault, exp_regular
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, price_num * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    green = 1_000 * EIGHTEEN_DECIMALS
    _give_green(green_token, credit_engine, user, green * 2)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    pre_supply = green_token.totalSupply()
    to_vault = psm.redeemGreen(green, vault, False, sender=user)
    after_psm_tx()
    to_eoa = psm.redeemGreen(green, user, False, sender=user)

    assert to_vault == exp_vault
    assert to_eoa == exp_regular
    # identical GREEN burned on both legs - only the payout rate differs
    assert pre_supply - green_token.totalSupply() == 2 * green


def test_g7_vault_redeem_skips_fee_even_at_one_hundred_percent(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    psm.setRedeemFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 2_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    # adjacent positive control: ordinary path is fully dead at 100%
    assert psm.getMaxRedeemableGreenAmount(user, False) == 0
    with boa.reverts("zero amount"):
        psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()

    got = psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, vault, False, sender=user)
    log = filter_logs(psm, "RedeemGreen")[0]
    assert got == 1_000 * SIX_DECIMALS
    assert log.usdcFee == 0

    psm.setRedeemFee(0, sender=switchboard_charlie.address)


def test_g7_vault_redeem_payout_never_exceeds_available_usdc_in_normal_band(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    """The min-cap / max-payout split is an inverse pair inside the normal price band."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 10_000_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    for price_num in (80, 90, 95, 99, 100, 101, 105, 120):
        mock_price_source.setPrice(charlie_token.address, price_num * EIGHTEEN_DECIMALS // 100)
        # top the reserve back up to an awkward, non-round number
        target = 7_777 * SIX_DECIMALS + 13
        cur = charlie_token.balanceOf(psm.address)
        if cur < target:
            charlie_token.mint(psm.address, target - cur, sender=governance.address)
        available = psm.getAvailableUsdc()
        got = psm.redeemGreen(MAX_UINT256, vault, False, sender=user)
        after_psm_tx()
        assert got <= available, f"overdraw at price {price_num}: {got} > {available}"
        if price_num >= 100:
            assert got == available          # 1:1 leg pays exactly the reserve
        else:
            assert available - got <= 2      # composed floors leave at most dust


def test_g7_vault_redeem_extreme_price_forced_one_breaks_the_inverse(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, pinned_undy
):
    """Previously PriceDesk's forced-`1` floor allowed 1 wei and broke the inverse.

    Dust USD value below `10**12` is now treated as zero capacity, so both the
    vault and regular redeem paths revert `zero amount` instead of paying.
    """
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)
    assert charlie_token.balanceOf(psm.address) == 0

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 1_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    charlie_token.mint(psm.address, 3, sender=governance.address)
    mock_price_source.setPrice(charlie_token.address, 300_000)
    assert 300_000 * 3 < ONE_USDC
    assert psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True) == 0
    pre_supply = green_token.totalSupply()
    pre_psm = charlie_token.balanceOf(psm.address)
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, vault, False, sender=user)
    after_psm_tx()
    assert green_token.totalSupply() == pre_supply
    assert charlie_token.balanceOf(psm.address) == pre_psm

    charlie_token.mint(psm.address, 1, sender=governance.address)
    mock_price_source.setPrice(charlie_token.address, 200_000)
    assert 200_000 * 4 < ONE_USDC
    assert psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True) == 0
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, vault, False, sender=user)
    after_psm_tx()
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, user, False, sender=user)

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)


# ------------------------------------------------------- round trips


@pytest.mark.parametrize("price_num", [95, 100, 105])
@pytest.mark.parametrize("fee", [0, 1_00])
def test_g7_round_trip_matrix_regular_and_vault(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, pinned_undy, price_num, fee
):
    """mint(regular) -> redeem(regular | vault), USDC in vs USDC back.

    Ordinary mint into a vault redeem is the break-even control: the vault
    `max()` is exactly the inverse of the mint `min()`, so no USDC is created.
    """
    psm = endaoment_psm
    price = price_num * EIGHTEEN_DECIMALS // 100
    mock_price_source.setPrice(charlie_token.address, price)
    _enable(psm, switchboard_charlie)
    if psm.mintFee() != fee:
        psm.setMintFee(fee, sender=switchboard_charlie.address)
    if psm.redeemFee() != fee:
        psm.setRedeemFee(fee, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    vault = pinned_undy(boa.env.generate_address())
    user = boa.env.generate_address()
    spend = 1_000 * SIX_DECIMALS
    charlie_token.mint(user, spend, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    green = psm.mintGreen(spend, user, False, sender=user)
    after_psm_tx()
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    back_regular = psm.redeemGreen(green, user, False, sender=user)
    after_psm_tx()
    assert back_regular <= spend, "regular round trip created USDC"

    # same GREEN quantity, vault recipient
    user2 = boa.env.generate_address()
    charlie_token.mint(user2, spend, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user2)
    green2 = psm.mintGreen(spend, user2, False, sender=user2)
    after_psm_tx()
    green_token.approve(psm.address, MAX_UINT256, sender=user2)
    pre_vault = charlie_token.balanceOf(vault)
    psm.redeemGreen(green2, vault, False, sender=user2)
    back_vault = charlie_token.balanceOf(vault) - pre_vault

    assert green == green2
    if fee == 0:
        assert back_vault == spend, "vault round trip is not break-even"
    else:
        assert back_vault <= spend
    assert back_vault >= back_regular

    if psm.mintFee() != 0:
        psm.setMintFee(0, sender=switchboard_charlie.address)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)


def test_g7_vault_redeem_above_peg_extracts_reserve_with_foreign_green(
    endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie,
    governance, credit_engine, charlie_token_vault, pinned_undy
):
    """Economic reachability: a beneficiary who owns the earn vault's shares.

    The vault here is a real ERC-4626 over the same USDC, so the extra USDC the
    PSM pays it is recoverable by whoever holds its shares.  GREEN is sourced
    outside the PSM (CreditEngine mint permission), which is the case the vault
    `max()` is *not* the inverse of any matching mint.
    """
    psm = endaoment_psm
    price = 105 * EIGHTEEN_DECIMALS // 100   # USDC at $1.05
    mock_price_source.setPrice(charlie_token.address, price)
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    vault = charlie_token_vault
    pinned_undy(vault.address)

    attacker = boa.env.generate_address()
    seed = 1 * SIX_DECIMALS
    charlie_token.mint(attacker, seed, sender=governance.address)
    charlie_token.approve(vault.address, MAX_UINT256, sender=attacker)
    shares = vault.deposit(seed, attacker, sender=attacker)
    assert vault.totalSupply() == shares      # attacker owns 100% of the vault

    green = 10_000 * EIGHTEEN_DECIMALS
    _give_green(green_token, credit_engine, attacker, green)
    green_token.approve(psm.address, MAX_UINT256, sender=attacker)

    psm.redeemGreen(green, vault.address, False, sender=attacker)
    after_psm_tx()
    recovered = vault.redeem(shares, attacker, attacker, sender=attacker)

    # control: the same GREEN redeemed straight to the attacker's EOA
    control = boa.env.generate_address()
    _give_green(green_token, credit_engine, control, green)
    green_token.approve(psm.address, MAX_UINT256, sender=control)
    control_usdc = psm.redeemGreen(green, control, False, sender=control)

    assert control_usdc == 9523809523                 # min() leg: $10,000 of USDC
    assert recovered - seed == 10_000 * SIX_DECIMALS  # max() leg: $10,500 of USDC
    assert recovered - seed - control_usdc == 476190477
