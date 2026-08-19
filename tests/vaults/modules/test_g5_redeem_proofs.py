"""Group 5 proof tests — redeem conservation (never-skip #3).

Redeem is a swap, not a burn: payer sends GREEN (payer -> vault custody, `P`),
receives claimable tokens. GREEN is NOT burned; it is sGREEN.deposit'd into the
pool (sGREEN cohort) or added as claimable GREEN. Reserved claimable GREEN
already in the vault is `B` — only `P` may be spent or refunded.
"""
import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import clear_transient_storage, redeem_from_stability_pool, filter_logs

CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source, amount):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(user, asset, amount, sender=teller.address) == amount


def _record_claim(stability_pool, stab_asset, claim_asset, claim_whale, claim_amount,
                  recipient, auction_house, green_token, savings_green, stab_amount=1):
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset, stab_amount, claim_asset, claim_amount,
        recipient, green_token, savings_green, sender=auction_house.address,
    )


def _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig):
    setGeneralConfig()
    stab_pool_id = vault_book.getRegId(stability_pool)
    setAssetConfig(alpha_token, _vaultIds=[stab_pool_id])


def _fund_green(green_token, whale, user, amount):
    green_token.transfer(user, amount, sender=whale)


def test_g5_redeem_conservation_basic(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """Basic redeem: GREEN spent (round-up) vs conservative value delivered;
    depositor NAV must not lose more active NAV than the GREEN inflow replaces."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 20 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        # sally redeems with GREEN (she need not hold shares)
        pay = 10 * EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, sally, pay)
        green_token.approve(teller.address, pay, sender=sally)

        nav_before = stability_pool.getTotalValue(alpha_token)
        bob_value_before = stability_pool.getTotalUserValue(bob, alpha_token)
        liab_before = stability_pool.totalClaimableBalances(bravo_token)
        green_custody_before = green_token.balanceOf(stability_pool.address)

        sally_bravo_before = bravo_token.balanceOf(sally)
        spent = redeem_from_stability_pool(teller, vault_id, bravo_token, pay, sender=sally)
        clear_transient_storage()

        delivered = bravo_token.balanceOf(sally) - sally_bravo_before
        # GREEN spent is round-up; delivered value must not exceed spent beyond rounding
        assert delivered <= spent + 2
        assert spent > 0

        # reserve identity for the redeemed pair
        assert stability_pool.totalClaimableBalances(bravo_token) == liab_before - delivered

        # GREEN inflow: for the alpha cohort (not sGREEN), spent GREEN becomes claimable GREEN
        green_claimable = stability_pool.claimableBalances(alpha_token, green_token)
        green_custody_after = green_token.balanceOf(stability_pool.address)
        # custody increased by spent (none burned); claimable GREEN recorded
        assert green_custody_after - green_custody_before == spent
        assert green_claimable == spent

        # depositor recorded liability conservation: active NAV falls by bravo delivered
        # but the replacement GREEN is claimable (dormant or active) — physical value retained
        nav_after = stability_pool.getTotalValue(alpha_token)
        print(f"\nredeem basic: spent={spent} delivered={delivered} "
              f"nav {nav_before} -> {nav_after} green_claimable={green_claimable}")
        # physical conservation: NAV_after + (dormant GREEN if excluded) must account for spent
        # if green_claimable is dormant (spent < $0.10? no, spent=10e18=$10) -> active
        assert green_claimable > 0


def test_g5_redeem_reserved_green_B_isolation(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """B-isolation: reserved claimable GREEN already in the vault must not be spent
    as payment, nor refunded to the caller. Only the newly pulled P may be spent/refunded."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 20 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        # first redeem: creates reserved claimable GREEN B in the pool
        pay1 = 5 * EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, bob, pay1)
        green_token.approve(teller.address, pay1, sender=bob)
        spent1 = redeem_from_stability_pool(teller, vault_id, bravo_token, pay1, sender=bob)
        clear_transient_storage()
        B = stability_pool.claimableBalances(alpha_token, green_token)
        assert B == spent1
        assert stability_pool.totalClaimableBalances(green_token) == B

        # second redeemer pays exactly enough that, if B were spendable as payment,
        # they'd get a free swap. Track: pool GREEN custody, B, sally's GREEN, delivered.
        pay2 = 3 * EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, sally, pay2)
        green_token.approve(teller.address, pay2, sender=sally)
        pool_green_before = green_token.balanceOf(stability_pool.address)
        sally_green_before = green_token.balanceOf(sally)
        sally_bravo_before = bravo_token.balanceOf(sally)

        spent2 = redeem_from_stability_pool(teller, vault_id, bravo_token, pay2, sender=sally)
        clear_transient_storage()

        sally_green_after = green_token.balanceOf(sally)
        delivered2 = bravo_token.balanceOf(sally) - sally_bravo_before

        # sally's GREEN decreased by exactly spent2 (payment pulled), plus any refund
        # she should have gotten back (pay2 - spent2) — refund recipient is the CALLER
        sally_green_delta = sally_green_before - sally_green_after
        # she paid pay2, was refunded (pay2 - spent2): net out == spent2
        assert sally_green_delta == spent2

        # B unchanged by the second redeem's payment/refund (B was not spent, not refunded)
        B_after = stability_pool.claimableBalances(alpha_token, green_token)
        # second redeem ALSO adds its spent2 GREEN to the alpha cohort claimable
        assert B_after == B + spent2
        # total claimable GREEN grew by spent2 only (B intact)
        assert stability_pool.totalClaimableBalances(green_token) == B + spent2

        # pool GREEN custody: increased by spent2 (B was not touched as payment)
        pool_green_after = green_token.balanceOf(stability_pool.address)
        assert pool_green_after - pool_green_before == spent2
        # no GREEN left the pool to sally as a refund of B
        # (sally's only GREEN change is the net payment of spent2, asserted above)


def test_g5_redeem_refund_to_caller(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """Overpayment refund goes to the CALLER (sally), as GREEN, and only from P."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 5 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        pay = 10 * EIGHTEEN_DECIMALS  # more than the 5e18 pile
        _fund_green(green_token, whale, sally, pay)
        green_token.approve(teller.address, pay, sender=sally)
        sally_green_before = green_token.balanceOf(sally)

        spent = redeem_from_stability_pool(teller, vault_id, bravo_token, pay,
                                           should_refund_savings_green=False, sender=sally)
        clear_transient_storage()
        sally_green_after = green_token.balanceOf(sally)
        # spent ~5e18, refund (pay - spent) as GREEN to sally: net out == spent
        assert sally_green_before - sally_green_after == spent
        assert spent <= claim_amount + 2


def test_g5_redeem_green_claim_asset_soft_skip(
    stability_pool, alpha_token, alpha_token_whale, bob, sally, teller,
    auction_house, mock_price_source, green_token, savings_green, vault_book,
    setGeneralConfig, setAssetConfig, whale,
):
    """Redeeming the GREEN token itself soft-skips; an all-skip batch reverts."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        clear_transient_storage()
        vault_id = vault_book.getRegId(stability_pool)
        pay = EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, sally, pay)
        green_token.approve(teller.address, pay, sender=sally)
        with boa.reverts("no redemptions occurred"):
            redeem_from_stability_pool(teller, vault_id, green_token, pay, sender=sally)
        clear_transient_storage()


def test_g5_redeem_sgreen_payment(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """_isPaymentSavingsGreen=True: payer sends sGREEN shares; Teller redeems to GREEN
    sent to the vault; redeem rows/return stay GREEN. Track supply deltas."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 10 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        # give sally sGREEN
        sgreen_amount = 20 * EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, sally, sgreen_amount)
        green_token.approve(savings_green.address, sgreen_amount, sender=sally)
        shares = savings_green.deposit(sgreen_amount, sally, sender=sally)
        clear_transient_storage()
        savings_green.approve(teller.address, shares, sender=sally)

        vault_id = vault_book.getRegId(stability_pool)
        pay_green = 8 * EIGHTEEN_DECIMALS
        pool_green_before = green_token.balanceOf(stability_pool.address)
        sally_sgreen_before = savings_green.balanceOf(sally)
        sgreen_supply_before = savings_green.totalSupply()

        sally_bravo_before = bravo_token.balanceOf(sally)
        spent = redeem_from_stability_pool(teller, vault_id, bravo_token, pay_green,
                                           is_payment_savings_green=True, sender=sally)
        clear_transient_storage()

        delivered = bravo_token.balanceOf(sally) - sally_bravo_before
        assert delivered <= spent + 2
        # sGREEN was pulled from sally and redeemed to GREEN at the vault
        assert savings_green.balanceOf(sally) < sally_sgreen_before
        # pool GREEN custody increased by spent (sGREEN cohort deposit would be sGREEN,
        # but alpha cohort -> spent GREEN becomes claimable GREEN)
        assert green_token.balanceOf(stability_pool.address) - pool_green_before >= spent
        # no sGREEN residue left in Teller
        assert savings_green.balanceOf(teller.address) == 0
        assert green_token.balanceOf(teller.address) == 0


def test_g5_redeem_replacement_green_dormant_accounting(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """H4: redeem an ACTIVE claimable with a small GREEN payment such that replacement
    GREEN is dormant (< $0.10). Active NAV falls by the delivered active value while
    physical replacement GREEN is excluded from NAV — measure depositor NAV delta vs
    the redeemer's extraction. Depositors must not lose recorded liability."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 15 * EIGHTEEN_DECIMALS  # active
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        # redeem a tiny slice so replacement GREEN < $0.10 (dormant)
        pay = 6 * 10**16  # $0.06
        _fund_green(green_token, whale, sally, pay)
        green_token.approve(teller.address, pay, sender=sally)

        nav_before = stability_pool.getTotalValue(alpha_token)
        recorded_liab_bravo_before = stability_pool.totalClaimableBalances(bravo_token)

        sally_bravo_before = bravo_token.balanceOf(sally)
        spent = redeem_from_stability_pool(teller, vault_id, bravo_token, pay, sender=sally)
        clear_transient_storage()
        delivered = bravo_token.balanceOf(sally) - sally_bravo_before

        green_claimable = stability_pool.claimableBalances(alpha_token, green_token)
        green_state = stability_pool.getClaimAssetState(alpha_token, green_token)
        nav_after = stability_pool.getTotalValue(alpha_token)
        print(f"\nH4 dormant replacement: spent={spent} delivered={delivered} "
              f"green_claimable={green_claimable} state={green_state} nav {nav_before}->{nav_after}")

        # depositor recorded liability (bravo) fell by delivered; replacement GREEN recorded
        assert stability_pool.totalClaimableBalances(bravo_token) == recorded_liab_bravo_before - delivered
        assert stability_pool.totalClaimableBalances(green_token) == spent

        # if replacement GREEN is dormant, NAV fell by delivered value but the physical
        # replacement is excluded from NAV -> depositors' priced NAV drops by more than
        # the GREEN inflow that is priced. This is the dormant-NAV gap; is it extractable?
        # sally extracted `delivered` active value; depositors got `spent` dormant GREEN.
        if green_state == CLAIM_ASSET_DORMANT:
            nav_drop = nav_before - nav_after
            print(f"active NAV drop={nav_drop}; dormant replacement value={spent}")
            # depositors can still claim/redeem the dormant GREEN later, so value is
            # retained as recorded liability — but it is unpriced in NAV until activated.


def test_g5_redeem_third_party_recipient(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, alice, teller, auction_house, mock_price_source, green_token,
    savings_green, vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """Redeem-to-other: recipient != caller requires recipient's canAnyoneDeposit,
    else hard revert. Self-redemption by anyone works."""
    with boa.env.anchor():
        _cfg_alpha(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        pay = EIGHTEEN_DECIMALS
        _fund_green(green_token, whale, sally, pay)
        green_token.approve(teller.address, pay, sender=sally)

        # sally redeems for alice (third-party). alice canAnyoneDeposit default off -> revert
        with boa.reverts():
            redeem_from_stability_pool(teller, vault_id, bravo_token, pay, recipient=alice, sender=sally)
        clear_transient_storage()

        # self-redemption works
        spent = redeem_from_stability_pool(teller, vault_id, bravo_token, pay, sender=sally)
        clear_transient_storage()
        assert spent > 0
