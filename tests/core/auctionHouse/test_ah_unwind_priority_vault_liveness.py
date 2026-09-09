"""Retired listed priority liq vaults are omitted from getGenLiqConfig.

`MissionControl.getGenLiqConfig` skips VaultBook entries that resolve to
`empty(address)`. AuctionHouse phase 1 still has no empty-vault guard; the
getter filter is what keeps a retired listed priority vault from reverting
every liquidation.
"""

import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import clear_transient_storage, filter_logs


def _configure(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    alpha_token,
    bravo_token,
    simple_id,
    rebase_id,
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
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    # bravo is a supported asset of the rebase vault, which stays empty so it
    # remains retirable -- this is the entry governance forgets to clear
    setAssetConfig(
        bravo_token,
        _vaultIds=[rebase_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)


def test_retiring_a_listed_priority_liq_vault_is_skipped_and_liquidation_succeeds(
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
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bob,
    alice,
    sally,
):
    simple_id = vault_book.getRegId(simple_erc20_vault)
    rebase_id = vault_book.getRegId(rebase_erc20_vault)
    _configure(
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        simple_id,
        rebase_id,
    )

    # the entry SwitchboardAlpha._validatePriorityVaults would accept today:
    # registered reg id, asset supported in that vault, not a stab/gov vault
    assert vault_book.isValidRegId(rebase_id)
    assert mission_control.isSupportedAssetInVault(rebase_id, bravo_token)
    assert not mission_control.isStabVaultId(rebase_id)
    mission_control.setPriorityLiqAssetVaults(
        [(rebase_id, bravo_token)],
        sender=switchboard_alpha.address,
    )
    assert vault_book.getAddr(rebase_id) == rebase_erc20_vault.address

    # ---- positive control: liquidation works while the entry resolves ----
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    performDeposit(alice, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.canLiquidateUser(alice)

    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    assert filter_logs(teller, "LiquidateUser")[0].numAuctionsStarted == 1
    assert ledger.userDebt(bob).inLiquidation
    assert ledger.hasFungibleAuctions(bob)

    # ---- governance retires the now-empty rebase vault, a legitimate action
    # that does NOT touch the stale priorityLiqAssetVaults entry ----
    assert vault_book.startAddressDisableInRegistry(
        rebase_id, sender=governance.address
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressDisableInRegistry(
        rebase_id, sender=governance.address
    )

    # isValidRegId still true, so the set-time validation would still pass,
    # but the address now resolves to zero
    assert vault_book.isValidRegId(rebase_id)
    assert vault_book.getAddr(rebase_id) == ZERO_ADDRESS

    assert credit_engine.canLiquidateUser(alice)

    with boa.env.anchor():
        clear_transient_storage()
        teller.liquidateUser(alice, False, sender=sally)
        assert filter_logs(teller, "LiquidateUser")[0].numAuctionsStarted == 1
        assert ledger.userDebt(alice).inLiquidation
        assert ledger.hasFungibleAuctions(alice)

    bob_debt = ledger.userDebt(bob)
    assert bob_debt.inLiquidation
    assert ledger.hasFungibleAuctions(bob)

    with boa.env.anchor():
        clear_transient_storage()
        teller.liquidateManyUsers([bob, alice], False, sender=sally)
        assert ledger.userDebt(alice).inLiquidation
        assert ledger.hasFungibleAuctions(alice)
        assert ledger.userDebt(bob).inLiquidation
        assert ledger.hasFungibleAuctions(bob)
        assert ledger.userDebt(bob).amount == bob_debt.amount


def test_phase_two_and_buy_both_guard_the_same_empty_vault_address(
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
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bob,
    sally,
):
    """Control: the same zeroed vault id is handled gracefully everywhere else.

    With no priority entry, a disabled vault id sitting in the borrower's own
    `Ledger.userVaults` list is skipped by phase 2 rather than reverting, which
    is what phase 1 should also do.
    """
    simple_id = vault_book.getRegId(simple_erc20_vault)
    rebase_id = vault_book.getRegId(rebase_erc20_vault)
    _configure(
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        simple_id,
        rebase_id,
    )
    # deliberately no priorityLiqAssetVaults entry
    mission_control.setPriorityLiqAssetVaults(
        [], sender=switchboard_alpha.address
    )

    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    assert vault_book.startAddressDisableInRegistry(
        rebase_id, sender=governance.address
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressDisableInRegistry(
        rebase_id, sender=governance.address
    )
    assert vault_book.getAddr(rebase_id) == ZERO_ADDRESS

    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.userDebt(bob).inLiquidation
    assert ledger.hasFungibleAuctions(bob)
