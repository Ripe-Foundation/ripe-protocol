import boa

from constants import EIGHTEEN_DECIMALS


ZERO_ASSET_VAULT_SOURCE = """
# @version 0.4.3

@view
@external
def doesVaultHaveAnyFunds() -> bool:
    return False

@view
@external
def numUserAssets(_user: address) -> uint256:
    return 0

@external
def deregisterUserAsset(_user: address, _asset: address) -> bool:
    raise "unexpected deregistration"
"""


def _install_zero_asset_replacement(vault_book, vault_id, governance):
    replacement = boa.loads(
        ZERO_ASSET_VAULT_SOURCE,
        name="zero_asset_replacement_vault",
    )
    assert vault_book.startAddressUpdateToRegistry(
        vault_id,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressUpdateToRegistry(
        vault_id,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == replacement.address
    return replacement


def _register_vault(vault_book, governance, vault, description):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        description,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    return vault_book.confirmNewAddressToRegistry(
        vault,
        sender=governance.address,
    )


def _add_healthy_replacement_peer(
    *,
    user,
    asset,
    asset_whale,
    setAssetConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    governance,
):
    healthy_vault_id = _register_vault(
        vault_book,
        governance,
        simple_erc20_vault,
        "healthy vault after stale replacement",
    )
    setAssetConfig(asset, _vaultIds=[healthy_vault_id])
    performDeposit(
        user,
        100 * EIGHTEEN_DECIMALS,
        asset,
        asset_whale,
        simple_erc20_vault,
    )
    return healthy_vault_id


def _create_stale_repointed_vault(
    *,
    user,
    asset,
    asset_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
):
    setGeneralConfig()
    setAssetConfig(asset)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(user, amount, asset, asset_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert ledger.isParticipatingInVault(user, vault_id)
    assert teller.withdraw(
        asset,
        amount,
        user,
        simple_erc20_vault,
        sender=user,
    ) == amount
    assert not simple_erc20_vault.doesVaultHaveAnyFunds()
    replacement = _install_zero_asset_replacement(
        vault_book,
        vault_id,
        governance,
    )
    assert ledger.isParticipatingInVault(user, vault_id)
    assert replacement.numUserAssets(user) == 0
    return vault_id, replacement


def test_credit_engine_skips_only_stale_repointed_zero_asset_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    credit_engine,
):
    _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )

    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert tuple(terms.debtTerms) == (0, 0, 0, 0, 0, 0)
    assert not terms.hasQuarantinedAsset


def test_credit_engine_values_healthy_vault_beside_stale_repointed_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    credit_engine,
):
    stale_vault_id, _ = _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    healthy_vault_id = _add_healthy_replacement_peer(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == 100 * EIGHTEEN_DECIMALS
    assert terms.totalMaxDebt == 50 * EIGHTEEN_DECIMALS
    assert terms.debtTerms.ltv == 50_00
    assert not terms.hasQuarantinedAsset
    assert ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.isParticipatingInVault(bob, healthy_vault_id)


def test_partial_and_full_repayment_continue_with_stale_repointed_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
):
    _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    _add_healthy_replacement_peer(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    debt = teller.borrow(40 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    partial = 10 * EIGHTEEN_DECIMALS
    green_token.approve(teller, debt, sender=bob)
    assert teller.repay(partial, bob, False, False, sender=bob)
    assert ledger.userDebt(bob).amount == debt - partial
    assert teller.repay(debt - partial, bob, False, False, sender=bob)
    assert ledger.userDebt(bob).amount == 0


def test_claimable_loot_skips_stale_repointed_zero_asset_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    lootbox,
):
    _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )

    assert lootbox.getClaimableLoot(bob) == 0


def test_claim_loot_removes_stale_vault_without_asset_deregistration(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id, replacement = _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )

    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert replacement.numUserAssets(bob) == 0
    assert not ledger.isParticipatingInVault(bob, vault_id)


def test_claim_loot_preserves_borrow_rewards_and_healthy_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    lootbox,
):
    stale_vault_id, _ = _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    healthy_vault_id = _add_healthy_replacement_peer(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    setGeneralDebtConfig()
    setRipeRewardsConfig(
        _arePointsEnabled=True,
        _ripePerBlock=10 * EIGHTEEN_DECIMALS,
        _borrowersAlloc=100_00,
        _stakersAlloc=0,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    teller.borrow(20 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    boa.env.time_travel(blocks=20)

    claimable_borrow = lootbox.getClaimableBorrowLoot(bob)
    assert claimable_borrow > 0
    assert lootbox.getClaimableLoot(bob) == claimable_borrow
    assert teller.claimLoot(bob, False, sender=bob) == claimable_borrow
    assert not ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.isParticipatingInVault(bob, healthy_vault_id)


def test_claim_loot_preserves_healthy_deposit_rewards_beside_stale_vault(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    lootbox,
):
    stale_vault_id, _ = _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )
    healthy_vault_id = _register_vault(
        vault_book,
        governance,
        simple_erc20_vault,
        "healthy deposit reward peer",
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[healthy_vault_id],
        _stakersPointsAlloc=100,
        _voterPointsAlloc=0,
    )
    setRipeRewardsConfig(
        _arePointsEnabled=True,
        _ripePerBlock=10 * EIGHTEEN_DECIMALS,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=20)

    claimable = lootbox.getClaimableLoot(bob)
    assert claimable > 0
    assert teller.claimLoot(bob, False, sender=bob) == claimable
    assert not ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.isParticipatingInVault(bob, healthy_vault_id)


def test_stale_vault_cleanup_capacity_defers_excess_without_revert(
    bob,
    setGeneralConfig,
    teller,
    ledger,
    vault_book,
    governance,
):
    setGeneralConfig()
    vault_ids = []
    for index in range(11):
        replacement = boa.loads(
            ZERO_ASSET_VAULT_SOURCE,
            name=f"zero_asset_capacity_vault_{index}",
        )
        vault_ids.append(
            _register_vault(
                vault_book,
                governance,
                replacement,
                f"zero asset capacity vault {index}",
            )
        )
        ledger.addVaultToUser(
            bob,
            vault_ids[-1],
            sender=teller.address,
        )

    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.numUserVaults(bob) == 2
    assert not any(
        ledger.isParticipatingInVault(bob, vault_id)
        for vault_id in vault_ids[:10]
    )
    assert ledger.isParticipatingInVault(bob, vault_ids[10])


def test_empty_vault_book_entry_keeps_existing_skip_and_no_cleanup_behavior(
    bob,
    setGeneralConfig,
    teller,
    ledger,
    credit_engine,
    lootbox,
):
    setGeneralConfig()
    empty_vault_id = 999
    ledger.addVaultToUser(
        bob,
        empty_vault_id,
        sender=teller.address,
    )

    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert lootbox.getClaimableLoot(bob) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.isParticipatingInVault(bob, empty_vault_id)


def test_reused_vault_id_does_not_affect_unrelated_user(
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
    ledger,
    simple_erc20_vault,
    vault_book,
    governance,
    credit_engine,
    lootbox,
):
    vault_id, _ = _create_stale_repointed_vault(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        performDeposit=performDeposit,
        teller=teller,
        ledger=ledger,
        simple_erc20_vault=simple_erc20_vault,
        vault_book=vault_book,
        governance=governance,
    )

    assert not ledger.isParticipatingInVault(alice, vault_id)
    assert credit_engine.getUserBorrowTerms(alice, False).collateralVal == 0
    assert lootbox.getClaimableLoot(alice) == 0
    assert teller.claimLoot(alice, False, sender=alice) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)
    assert ledger.isParticipatingInVault(bob, vault_id)
