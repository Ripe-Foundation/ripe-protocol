import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


SIMPLE_VAULT_ID = 3
REBASE_VAULT_ID = 4


def _deploy_replacement(ripe_hq, name):
    return boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq,
        name=name,
    )


def _start_retirement(
    action_kind,
    vault_book,
    governance,
    vault_id,
    replacement=None,
    sender=None,
):
    caller = governance.address if sender is None else sender
    if action_kind == "update":
        return vault_book.startAddressUpdateToRegistry(
            vault_id,
            replacement,
            sender=caller,
        )
    return vault_book.startAddressDisableInRegistry(
        vault_id,
        sender=caller,
    )


def _confirm_retirement(action_kind, vault_book, governance, vault_id, sender=None):
    caller = governance.address if sender is None else sender
    if action_kind == "update":
        return vault_book.confirmAddressUpdateToRegistry(vault_id, sender=caller)
    return vault_book.confirmAddressDisableInRegistry(vault_id, sender=caller)


def _pending_retirement(action_kind, vault_book, vault_id):
    if action_kind == "update":
        return vault_book.pendingAddrUpdate(vault_id)
    return vault_book.pendingAddrDisable(vault_id)


def _failed_confirmation_state(
    action_kind,
    vault_book,
    vault,
    replacement,
    vault_id,
    token,
    green_token,
    user,
    ledger,
):
    replacement_reverse = 0
    replacement_is_valid = False
    if replacement is not None:
        replacement_reverse = vault_book.getRegId(replacement)
        replacement_is_valid = vault_book.isValidAddr(replacement)

    return {
        "address_info": vault_book.getAddrInfo(vault_id),
        "old_reverse_mapping": vault_book.getRegId(vault),
        "old_is_valid": vault_book.isValidAddr(vault),
        "replacement_reverse_mapping": replacement_reverse,
        "replacement_is_valid": replacement_is_valid,
        "num_addresses": vault_book.getNumAddrs(),
        "pending": _pending_retirement(action_kind, vault_book, vault_id),
        "user_recorded_balance": vault.getTotalAmountForUser(user, token),
        "vault_recorded_balance": vault.totalBalances(token),
        "vault_token_custody": token.balanceOf(vault),
        "user_token_balance": token.balanceOf(user),
        "user_green_balance": green_token.balanceOf(user),
        "deposit_ledger": ledger.getDepositLedgerData(user, vault_id),
        "vault_index": ledger.indexOfVault(user, vault_id),
        "first_user_vault": ledger.userVaults(user, 1),
        "user_debt": ledger.userDebt(user),
        "total_debt": ledger.totalDebt(),
        "borrow_points": ledger.getBorrowPointsBundle(user),
        "deposit_points": ledger.getDepositPointsBundle(user, vault_id, token),
        "ripe_rewards": ledger.getRipeRewardsBundle(),
    }


def _non_routing_asset_config(config):
    return (
        config.stakersPointsAlloc,
        config.voterPointsAlloc,
        config.perUserDepositLimit,
        config.globalDepositLimit,
        config.minDepositBalance,
        config.debtTerms,
        config.shouldBurnAsPayment,
        config.shouldTransferToEndaoment,
        config.shouldSwapInStabPools,
        config.shouldAuctionInstantly,
        config.canDeposit,
        config.canWithdraw,
        config.canRedeemCollateral,
        config.canRedeemInStabPool,
        config.canBuyInAuction,
        config.canClaimInStabPool,
        config.specialStabPoolId,
        config.customAuctionParams,
        config.whitelist,
        config.isNft,
    )


def _debt_risk_state(credit_engine, ledger, user, vault_id, asset, vault):
    terms = credit_engine.getUserBorrowTerms(user, True)
    return {
        "collateral_value": credit_engine.getCollateralValue(user),
        "total_max_debt": terms.totalMaxDebt,
        "stored_debt": ledger.userDebt(user),
        "has_good_debt_health": credit_engine.hasGoodDebtHealth(user),
        "can_liquidate": credit_engine.canLiquidateUser(user),
        "max_withdrawable": credit_engine.getMaxWithdrawableForAsset(
            user,
            vault_id,
            asset,
            vault,
        ),
    }


def test_confirm_new_address_to_registry_lifecycle_still_works(
    ripe_hq,
    governance,
    vault_book,
    bob,
):
    candidate = _deploy_replacement(ripe_hq, "new_address_candidate")
    description = "New address regression"
    expected_id = vault_book.getNumAddrs() + 1

    assert vault_book.startAddNewAddressToRegistry(
        candidate,
        description,
        sender=governance.address,
    )
    pending = vault_book.pendingNewAddr(candidate)
    assert pending.confirmBlock != 0

    with boa.reverts("no perms"):
        vault_book.confirmNewAddressToRegistry(candidate, sender=bob)
    with boa.reverts("time lock not reached"):
        vault_book.confirmNewAddressToRegistry(
            candidate,
            sender=governance.address,
        )

    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmNewAddressToRegistry(
        candidate,
        sender=governance.address,
    ) == expected_id

    info = vault_book.getAddrInfo(expected_id)
    assert info.addr == candidate.address
    assert info.version == 1
    assert info.description == description
    assert vault_book.getRegId(candidate) == expected_id
    assert vault_book.isValidAddr(candidate)
    assert vault_book.pendingNewAddr(candidate).confirmBlock == 0


@pytest.mark.parametrize("action_kind", ["update", "disable"])
def test_funded_confirmation_reverts_and_preserves_pending_and_protocol_state(
    action_kind,
    ripe_hq,
    governance,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    ledger,
):
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    replacement = None
    if action_kind == "update":
        replacement = _deploy_replacement(ripe_hq, "funded_update_replacement")

    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert vault_id == SIMPLE_VAULT_ID
    assert _start_retirement(
        action_kind,
        vault_book,
        governance,
        vault_id,
        replacement,
    )

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())

    state_before = _failed_confirmation_state(
        action_kind,
        vault_book,
        simple_erc20_vault,
        replacement,
        vault_id,
        alpha_token,
        green_token,
        bob,
        ledger,
    )
    with boa.reverts("vault has funds"):
        _confirm_retirement(action_kind, vault_book, governance, vault_id)
    state_after = _failed_confirmation_state(
        action_kind,
        vault_book,
        simple_erc20_vault,
        replacement,
        vault_id,
        alpha_token,
        green_token,
        bob,
        ledger,
    )

    assert state_after == state_before
    assert state_after["address_info"].addr == simple_erc20_vault.address
    assert state_after["address_info"].version == 1
    assert state_after["old_reverse_mapping"] == vault_id
    assert state_after["old_is_valid"]
    assert state_after["pending"].confirmBlock != 0
    if replacement is not None:
        assert state_after["replacement_reverse_mapping"] == 0
        assert not state_after["replacement_is_valid"]


@pytest.mark.parametrize("action_kind", ["update", "disable"])
def test_funded_pending_retirement_can_be_retried_after_full_teller_withdrawal(
    action_kind,
    ripe_hq,
    governance,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    replacement = None
    if action_kind == "update":
        replacement = _deploy_replacement(ripe_hq, "drained_update_replacement")

    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert _start_retirement(
        action_kind,
        vault_book,
        governance,
        vault_id,
        replacement,
    )
    pending = _pending_retirement(action_kind, vault_book, vault_id)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    with boa.reverts("vault has funds"):
        _confirm_retirement(action_kind, vault_book, governance, vault_id)
    assert _pending_retirement(action_kind, vault_book, vault_id) == pending

    assert teller.withdraw(
        alpha_token,
        deposit_amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == deposit_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.totalBalances(alpha_token) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert not simple_erc20_vault.doesVaultHaveAnyFunds()

    assert _confirm_retirement(action_kind, vault_book, governance, vault_id)
    assert _pending_retirement(action_kind, vault_book, vault_id).confirmBlock == 0
    if action_kind == "update":
        assert vault_book.getAddr(vault_id) == replacement.address
        assert vault_book.getRegId(replacement) == vault_id
        assert vault_book.getRegId(simple_erc20_vault) == 0
    else:
        assert vault_book.getAddr(vault_id) == ZERO_ADDRESS
        assert vault_book.getRegId(simple_erc20_vault) == 0


def test_governed_deposit_route_removal_preserves_debt_risk_and_allows_retirement(
    ripe_hq,
    governance,
    vault_book,
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    performDeposit,
    mission_control,
    switchboard_bravo,
    mock_price_source,
    credit_engine,
    ledger,
):
    setGeneralConfig()
    debt_terms = createDebtTerms()
    setAssetConfig(
        alpha_token,
        _vaultIds=[SIMPLE_VAULT_ID, REBASE_VAULT_ID],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _perUserDepositLimit=1_000 * EIGHTEEN_DECIMALS,
        _globalDepositLimit=10_000 * EIGHTEEN_DECIMALS,
        _debtTerms=debt_terms,
    )
    setGeneralDebtConfig()

    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert vault_id == SIMPLE_VAULT_ID
    replacement = _deploy_replacement(ripe_hq, "debt_retirement_replacement")
    assert vault_book.startAddressUpdateToRegistry(
        vault_id,
        replacement,
        sender=governance.address,
    )
    pending_update = vault_book.pendingAddrUpdate(vault_id)

    bob_deposit = 100 * EIGHTEEN_DECIMALS
    alice_deposit = 40 * EIGHTEEN_DECIMALS
    performDeposit(bob, bob_deposit, alpha_token, alpha_token_whale)
    performDeposit(alice, alice_deposit, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    borrow_amount = 25 * EIGHTEEN_DECIMALS
    assert teller.borrow(borrow_amount, bob, False, sender=bob) == borrow_amount
    assert ledger.userDebt(bob).amount == borrow_amount

    config_before = mission_control.assetConfig(alpha_token)
    assert list(config_before.vaultIds) == [SIMPLE_VAULT_ID, REBASE_VAULT_ID]
    assert config_before.stakersPointsAlloc == 0
    assert config_before.voterPointsAlloc == 0
    deposit_route_action = switchboard_bravo.setAssetDepositParams(
        alpha_token,
        [REBASE_VAULT_ID],
        config_before.stakersPointsAlloc,
        config_before.voterPointsAlloc,
        config_before.perUserDepositLimit,
        config_before.globalDepositLimit,
        config_before.minDepositBalance,
        sender=governance.address,
    )

    confirmation_block = max(
        pending_update.confirmBlock,
        switchboard_bravo.getActionConfirmationBlock(deposit_route_action),
    )
    if boa.env.evm.patch.block_number < confirmation_block:
        boa.env.time_travel(
            blocks=confirmation_block - boa.env.evm.patch.block_number,
        )

    with boa.reverts("vault has funds"):
        vault_book.confirmAddressUpdateToRegistry(
            vault_id,
            sender=governance.address,
        )
    assert vault_book.pendingAddrUpdate(vault_id) == pending_update

    risk_before = _debt_risk_state(
        credit_engine,
        ledger,
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault,
    )
    config_immediately_before = mission_control.assetConfig(alpha_token)
    block_before = boa.env.evm.patch.block_number
    timestamp_before = boa.env.evm.patch.timestamp
    assert switchboard_bravo.executePendingAction(
        deposit_route_action,
        sender=governance.address,
    )
    assert boa.env.evm.patch.block_number == block_before
    assert boa.env.evm.patch.timestamp == timestamp_before
    risk_after = _debt_risk_state(
        credit_engine,
        ledger,
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault,
    )

    config_after = mission_control.assetConfig(alpha_token)
    assert list(config_immediately_before.vaultIds) == [
        SIMPLE_VAULT_ID,
        REBASE_VAULT_ID,
    ]
    assert list(config_after.vaultIds) == [REBASE_VAULT_ID]
    assert _non_routing_asset_config(config_after) == _non_routing_asset_config(
        config_immediately_before,
    )
    assert risk_after == risk_before
    assert risk_after["collateral_value"] == bob_deposit
    assert risk_after["total_max_debt"] == bob_deposit // 2
    assert risk_after["stored_debt"].amount == borrow_amount
    assert risk_after["has_good_debt_health"]
    assert not risk_after["can_liquidate"]
    assert 0 < risk_after["max_withdrawable"] < bob_deposit

    other_vault_deposit = 10 * EIGHTEEN_DECIMALS
    assert alpha_token.transfer(sally, other_vault_deposit, sender=alpha_token_whale)
    assert alpha_token.approve(teller, other_vault_deposit, sender=sally)
    with boa.reverts("vault does not support asset"):
        teller.deposit(
            alpha_token,
            other_vault_deposit,
            sally,
            simple_erc20_vault,
            sender=sally,
        )
    assert teller.deposit(
        alpha_token,
        other_vault_deposit,
        sally,
        rebase_erc20_vault,
        sender=sally,
    ) == other_vault_deposit

    constrained_withdrawal = teller.withdraw(
        alpha_token,
        MAX_UINT256,
        bob,
        simple_erc20_vault,
        sender=bob,
    )
    assert constrained_withdrawal == risk_before["max_withdrawable"]
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) != 0

    debt_amount = credit_engine.getUserDebtAmount(bob)
    green_balance = green_token.balanceOf(bob)
    if green_balance < debt_amount:
        assert green_token.transfer(bob, debt_amount - green_balance, sender=whale)
    assert green_token.approve(teller, debt_amount, sender=bob)
    assert teller.repay(debt_amount, bob, False, False, sender=bob)
    assert ledger.userDebt(bob).amount == 0

    bob_remaining = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert teller.withdraw(
        alpha_token,
        bob_remaining,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == bob_remaining
    assert teller.withdraw(
        alpha_token,
        alice_deposit,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alice_deposit

    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(alice, alpha_token) == 0
    assert simple_erc20_vault.totalBalances(alpha_token) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert not simple_erc20_vault.doesVaultHaveAnyFunds()
    assert vault_book.pendingAddrUpdate(vault_id) == pending_update

    assert vault_book.confirmAddressUpdateToRegistry(
        vault_id,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == replacement.address
    assert vault_book.getRegId(simple_erc20_vault) == 0
    assert vault_book.getRegId(replacement) == vault_id


@pytest.mark.parametrize("action_kind", ["update", "disable"])
def test_untracked_direct_token_donation_does_not_block_confirmation(
    action_kind,
    ripe_hq,
    governance,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
):
    replacement = None
    if action_kind == "update":
        replacement = _deploy_replacement(ripe_hq, "donation_update_replacement")

    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert _start_retirement(
        action_kind,
        vault_book,
        governance,
        vault_id,
        replacement,
    )

    donation = 7 * EIGHTEEN_DECIMALS
    assert alpha_token.transfer(
        simple_erc20_vault,
        donation,
        sender=alpha_token_whale,
    )
    assert simple_erc20_vault.totalBalances(alpha_token) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == donation
    assert not simple_erc20_vault.doesVaultHaveAnyFunds()

    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert _confirm_retirement(action_kind, vault_book, governance, vault_id)
    if action_kind == "update":
        assert vault_book.getAddr(vault_id) == replacement.address
    else:
        assert vault_book.getAddr(vault_id) == ZERO_ADDRESS


@pytest.mark.parametrize("action_kind", ["update", "disable"])
def test_confirmation_checks_permission_before_funded_vault_state(
    action_kind,
    ripe_hq,
    governance,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
):
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    replacement = None
    if action_kind == "update":
        replacement = _deploy_replacement(ripe_hq, "permission_update_replacement")

    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert _start_retirement(
        action_kind,
        vault_book,
        governance,
        vault_id,
        replacement,
    )
    pending = _pending_retirement(action_kind, vault_book, vault_id)
    performDeposit(
        bob,
        10 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())

    with boa.reverts("no perms"):
        _confirm_retirement(
            action_kind,
            vault_book,
            governance,
            vault_id,
            sender=bob,
        )

    with boa.reverts("vault has funds"):
        _start_retirement(
            action_kind,
            vault_book,
            governance,
            vault_id,
            replacement,
            sender=bob,
        )
    with boa.reverts("vault has funds"):
        _confirm_retirement(action_kind, vault_book, governance, vault_id)
    assert _pending_retirement(action_kind, vault_book, vault_id) == pending
