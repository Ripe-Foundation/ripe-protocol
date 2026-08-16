import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, MAX_UINT256


PRECISION_18 = 10 ** 9


def _enable_gen_rewards(setRipeRewardsConfig):
    setRipeRewardsConfig(
        True,
        10,
        0,
        0,
        0,
        HUNDRED_PERCENT,
    )


def _normalized(amount):
    return amount // PRECISION_18


def test_sc14_swap_collateral_checkpoints_sender(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    deleverage,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    governance,
    bob,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    _enable_gen_rewards(setRipeRewardsConfig)
    terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00)
    setAssetConfig(
        alpha_token,
        _debtTerms=terms,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )
    setAssetConfig(
        bravo_token,
        _debtTerms=createDebtTerms(_ltv=75_00, _redemptionThreshold=80_00, _liqThreshold=85_00),
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)
    usd_before = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    assert usd_before > 0

    swap_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(governance, swap_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, swap_amount, sender=governance.address)

    elapsed = 15
    boa.env.time_travel(blocks=elapsed)
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        swap_amount,
        sender=governance.address,
    )
    assert withdrawn == swap_amount
    assert deposited == swap_amount

    remaining = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert remaining == deposit_amount - swap_amount
    assert sender.lastBalance == _normalized(remaining)
    assert sender.lastBalance != before.lastBalance
    assert sender.balancePoints == before.lastBalance * elapsed
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == (
        remaining // EIGHTEEN_DECIMALS
    )


def test_sc14_endaoment_deleverage_checkpoints_sender(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    setupDeleverage,
    setup_priority_configs,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    _enable_gen_rewards(setRipeRewardsConfig)
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=createDebtTerms(
            _ltv=80_00,
            _redemptionThreshold=85_00,
            _liqThreshold=90_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token)],
    )

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    borrow_amount = 200 * EIGHTEEN_DECIMALS
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=deposit_amount,
        borrow_amount=borrow_amount,
        get_sgreen=False,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)

    elapsed = 12
    boa.env.time_travel(blocks=elapsed)
    repaid = teller.deleverageManyUsers([(bob, 0)], sender=switchboard_alpha.address)
    assert repaid > 0

    remaining = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert remaining < deposit_amount
    assert sender.lastBalance == _normalized(remaining)
    assert sender.balancePoints == before.lastBalance * elapsed
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == (
        remaining // EIGHTEEN_DECIMALS
    )
