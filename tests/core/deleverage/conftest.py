"""
Fixtures and helper functions for Deleverage.vy tests
"""
import pytest
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture
def setupDeleverage(
    teller,
    performDeposit,
    mock_price_source,
):
    def setupDeleverage(
        user,
        collateral_token,
        collateral_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    ):
        # IMPORTANT: Set initial price BEFORE deposit/borrow
        original_price = 1 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(collateral_token, original_price)

        # Deposit collateral
        performDeposit(user, deposit_amount, collateral_token, collateral_whale)

        # Borrow GREEN (or sGREEN)
        teller.borrow(borrow_amount, user, get_sgreen, sender=user)

    return setupDeleverage


@pytest.fixture
def setup_priority_configs(
    mission_control,
    vault_book,
    stability_pool,
    switchboard_alpha,
):
    def setup_priority_configs(priority_stab_assets=None, priority_liq_assets=None):
        stab_id = vault_book.getRegId(stability_pool)

        # Configure priority stability vaults
        if priority_stab_assets:
            stab_vault_data = []
            for vault, asset in priority_stab_assets:
                vault_id = vault_book.getRegId(vault) if vault != stability_pool else stab_id
                stab_vault_data.append((vault_id, asset))

            mission_control.setPriorityStabVaults(
                stab_vault_data,
                sender=switchboard_alpha.address
            )

        # Configure priority liquidation assets
        if priority_liq_assets:
            liq_asset_data = []
            for vault, asset in priority_liq_assets:
                vault_id = vault_book.getRegId(vault) if vault != stability_pool else stab_id
                liq_asset_data.append((vault_id, asset))

            mission_control.setPriorityLiqAssetVaults(
                liq_asset_data,
                sender=switchboard_alpha.address
            )

        return stab_id

    return setup_priority_configs
