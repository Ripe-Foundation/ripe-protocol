import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import clear_transient_storage, filter_logs


def test_retiring_listed_empty_priority_stab_pool_is_skipped_and_liquidation_succeeds(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    mission_control,
    switchboard_alpha,
    vault_book,
    governance,
    stability_pool,
    savings_green,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)], sender=switchboard_alpha.address
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    for user in (bob, alice):
        performDeposit(
            user,
            200 * EIGHTEEN_DECIMALS,
            alpha_token,
            alpha_token_whale,
        )
        teller.borrow(100 * EIGHTEEN_DECIMALS, user, False, sender=user)

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS // 2)
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.canLiquidateUser(alice)
    assert vault_book.getAddr(stab_id) == stability_pool.address
    assert not stability_pool.doesVaultHaveAnyFunds()

    # Control: the configured but empty live pool returns false from its
    # capability probe, and liquidation falls back to an ordinary auction.
    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    assert len(filter_logs(teller, "LiquidateUser")) == 1
    assert ledger.userDebt(bob).inLiquidation
    assert ledger.hasFungibleAuctions(bob)

    assert vault_book.startAddressDisableInRegistry(
        stab_id, sender=governance.address
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressDisableInRegistry(
        stab_id, sender=governance.address
    )
    assert vault_book.getAddr(stab_id) == ZERO_ADDRESS
    assert credit_engine.canLiquidateUser(alice)

    clear_transient_storage()
    teller.liquidateUser(alice, False, sender=sally)
    assert len(filter_logs(teller, "LiquidateUser")) == 1
    assert ledger.userDebt(alice).inLiquidation
    assert ledger.hasFungibleAuctions(alice)
