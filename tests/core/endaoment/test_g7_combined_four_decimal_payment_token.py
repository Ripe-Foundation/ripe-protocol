"""Finding 1: constructor rejects a non-6-decimal payment token."""

import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


ONE_GREEN = EIGHTEEN_DECIMALS
ONE_USDC = 10**6


def test_g7_four_decimal_mint_underpays_and_vault_redeem_overpays(
    ripe_hq_deploy,
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    governance,
    mock_price_source,
):
    tok4 = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "T4",
        "T4",
        4,
        1_000_000_000,
        name="g7_combined_4dp_token",
    )
    with boa.reverts("usdc must be 6 decimals"):
        boa.load(
            "contracts/core/EndaomentPSM.vy",
            ripe_hq_deploy,
            100,
            0,
            100_000 * ONE_GREEN,
            0,
            100_000 * ONE_GREEN,
            tok4.address,
            0,
            ZERO_ADDRESS,
            name="g7_combined_4dp_psm",
        )

    mock_price_source.setPrice(charlie_token.address, ONE_GREEN)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    user = boa.env.generate_address()
    charlie_token.mint(user, ONE_USDC, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, ONE_USDC, sender=user)
    assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) == ONE_GREEN
    after_psm_tx()
    green_token.approve(endaoment_psm.address, ONE_GREEN, sender=user)
    assert endaoment_psm.redeemGreen(ONE_GREEN, user, False, sender=user) == ONE_USDC
    after_psm_tx()
