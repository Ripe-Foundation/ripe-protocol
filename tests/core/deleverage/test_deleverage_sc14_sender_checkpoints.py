from pathlib import Path

import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT


PRECISION_18 = 10**9


def _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, blocked_user):
    source = Path("contracts/core/Lootbox.vy").read_text()
    needle = """@internal
def _updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys,
):
"""
    assert source.count(needle) == 1
    source = source.replace(
        needle,
        needle + f"    assert _user != {blocked_user} # dev: user checkpoint blocked\n",
        1,
    )
    mutant = boa.loads(
        source,
        ripe_hq.address,
        43_200,
        43_200,
        100 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        name="lootbox_user_checkpoint_trap",
    )
    boa.env.set_code(lootbox.address, bytes(boa.env.get_code(mutant.address)))


def _enable_gen_rewards(setRipeRewardsConfig):
    setRipeRewardsConfig(True, 10, 0, 0, 0, HUNDRED_PERCENT)


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
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00),
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
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)

    swap_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(governance, swap_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, swap_amount, sender=governance.address)

    elapsed = 15
    boa.env.time_travel(blocks=elapsed)
    gas_before = boa.env.get_gas_used()
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        swap_amount,
        sender=governance.address,
    )
    gas_used = boa.env.get_gas_used() - gas_before
    print("SC14_SWAP_COLLATERAL_GAS", gas_used)
    # Measured 828,782 at this source tree; keep about 20% regression headroom.
    assert gas_used < 1_000_000
    assert withdrawn == swap_amount
    assert deposited == swap_amount

    remaining = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sender_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert remaining == deposit_amount - swap_amount
    assert sender_points.lastBalance == _normalized(remaining)
    assert sender_points.lastBalance != before.lastBalance
    assert sender_points.balancePoints == before.lastBalance * elapsed
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == (
        remaining // EIGHTEEN_DECIMALS
    )


def test_sc14_swap_collateral_sender_checkpoint_revert_is_atomic(
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
    ripe_hq,
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
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00),
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
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    swap_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(governance, swap_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, swap_amount, sender=governance.address)
    state = {
        "user_balance": simple_erc20_vault.userBalances(bob, alpha_token),
        "vault_tokens": alpha_token.balanceOf(simple_erc20_vault),
        "recipient_tokens": alpha_token.balanceOf(governance),
        "user_points": ledger.userDepositPoints(bob, vault_id, alpha_token),
        "asset_points": ledger.assetDepositPoints(vault_id, alpha_token),
        "global_points": ledger.globalDepositPoints(),
    }

    _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, bob)
    # The trap is the first checkpoint statement, so this revert proves the flow
    # reached the blocked user's checkpoint before completing the withdrawal.
    with boa.reverts():
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            swap_amount,
            sender=governance.address,
        )

    assert simple_erc20_vault.userBalances(bob, alpha_token) == state["user_balance"]
    assert alpha_token.balanceOf(simple_erc20_vault) == state["vault_tokens"]
    assert alpha_token.balanceOf(governance) == state["recipient_tokens"]
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == state["user_points"]
    assert ledger.assetDepositPoints(vault_id, alpha_token) == state["asset_points"]
    assert ledger.globalDepositPoints() == state["global_points"]


def test_sc14_endaoment_deleverage_checkpoints_sender(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=deposit_amount,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)

    elapsed = 12
    boa.env.time_travel(blocks=elapsed)
    gas_before = boa.env.get_gas_used()
    repaid = teller.deleverageManyUsers([(bob, 0)], sender=switchboard_alpha.address)
    gas_used = boa.env.get_gas_used() - gas_before
    print("SC14_DELEVERAGE_GAS", gas_used)
    # Measured 426,352 at this source tree; keep about 20% regression headroom.
    assert gas_used < 525_000
    assert repaid > 0

    remaining = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sender_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert remaining < deposit_amount
    assert sender_points.lastBalance == _normalized(remaining)
    assert sender_points.balancePoints == before.lastBalance * elapsed
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == (
        remaining // EIGHTEEN_DECIMALS
    )
