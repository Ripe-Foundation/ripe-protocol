import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ONE_YEAR


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


SETTLEABLE_ZERO_ASSET_VAULT_SOURCE = """
# @version 0.4.3

@view
@external
def doesVaultHaveAnyFunds() -> bool:
    return False

@view
@external
def numUserAssets(_user: address) -> uint256:
    return 0

@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return 0

@view
@external
def doesUserHaveBalance(_user: address, _asset: address) -> bool:
    return False

@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return 0

@external
def deregisterUserAsset(_user: address, _asset: address) -> bool:
    raise "unexpected deregistration"
"""


BORROWABLE_STALE_VAULT_SOURCE = """
# @version 0.4.3

USER: immutable(address)
ASSET: immutable(address)
AMOUNT: immutable(uint256)
hasFunds: bool

@deploy
def __init__(_user: address, _asset: address, _amount: uint256):
    USER = _user
    ASSET = _asset
    AMOUNT = _amount
    self.hasFunds = True

@view
@external
def doesVaultHaveAnyFunds() -> bool:
    return self.hasFunds

@external
def setDoesVaultHaveAnyFunds(_hasFunds: bool):
    self.hasFunds = _hasFunds

@view
@external
def numUserAssets(_user: address) -> uint256:
    if _user == USER:
        return 2
    return 1

@view
@external
def getUserAssetAndAmountAtIndex(
    _user: address,
    _index: uint256,
) -> (address, uint256):
    if _user == USER and _index == 1:
        return ASSET, AMOUNT
    return empty(address), 0

@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    if _asset == ASSET:
        return AMOUNT
    return 0

@view
@external
def doesUserHaveBalance(_user: address, _asset: address) -> bool:
    return _user == USER and _asset == ASSET
"""


def _set_vault_pointer(vault_book, vault_id, vault, governance):
    assert vault_book.startAddressUpdateToRegistry(
        vault_id,
        vault,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressUpdateToRegistry(
        vault_id,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == vault.address


def _install_zero_asset_replacement(vault_book, vault_id, governance):
    replacement = boa.loads(
        ZERO_ASSET_VAULT_SOURCE,
        name="zero_asset_replacement_vault",
    )
    _set_vault_pointer(vault_book, vault_id, replacement, governance)
    return replacement


def _install_settleable_zero_asset_replacement(
    vault_book,
    vault_id,
    governance,
):
    replacement = boa.loads(
        SETTLEABLE_ZERO_ASSET_VAULT_SOURCE,
        name="settleable_zero_asset_replacement_vault",
    )
    _set_vault_pointer(vault_book, vault_id, replacement, governance)
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


def _create_stale_only_borrower(
    *,
    user,
    asset,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    ledger,
    vault_book,
    governance,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=10_00,
        _daowry=1_00,
    )
    source_vault = boa.loads(
        BORROWABLE_STALE_VAULT_SOURCE,
        user,
        asset,
        100 * EIGHTEEN_DECIMALS,
        name="borrowable_stale_source_vault",
    )
    vault_id = _register_vault(
        vault_book,
        governance,
        source_vault,
        "borrowable source before stale replacement",
    )
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _debtTerms=debt_terms,
    )
    setGeneralDebtConfig()
    ledger.addVaultToUser(
        user,
        vault_id,
        sender=teller.address,
    )
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    borrowed = teller.borrow(
        40 * EIGHTEEN_DECIMALS,
        user,
        False,
        sender=user,
    )
    stored_terms = tuple(ledger.userDebt(user).debtTerms)
    source_vault.setDoesVaultHaveAnyFunds(False)
    assert not source_vault.doesVaultHaveAnyFunds()
    replacement = _install_zero_asset_replacement(
        vault_book,
        vault_id,
        governance,
    )
    assert replacement.numUserAssets(user) == 0
    return vault_id, source_vault, borrowed, stored_terms


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


def test_stale_only_partial_repay_and_updates_preserve_terms_and_interest(
    bob,
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    green_token,
    whale,
    ledger,
    credit_engine,
    vault_book,
    governance,
):
    vault_id, source_vault, borrowed, stored_terms = _create_stale_only_borrower(
        user=bob,
        asset=alpha_token,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        mock_price_source=mock_price_source,
        teller=teller,
        ledger=ledger,
        vault_book=vault_book,
        governance=governance,
    )

    partial = borrowed // 4
    expected_after_repay = credit_engine.getUserDebtAmount(bob) - partial
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert not teller.repay(partial, bob, False, False, sender=bob)
    after_repay = ledger.userDebt(bob)
    assert after_repay.amount == expected_after_repay
    assert tuple(after_repay.debtTerms) == stored_terms

    boa.env.time_travel(seconds=ONE_YEAR)
    expected_stale_amount = credit_engine.getUserDebtAmount(bob)
    assert expected_stale_amount > after_repay.amount
    assert not credit_engine.updateDebtForUser(
        bob,
        sender=credit_engine.address,
    )
    after_stale_update = ledger.userDebt(bob)
    assert after_stale_update.amount == expected_stale_amount
    assert tuple(after_stale_update.debtTerms) == stored_terms

    _set_vault_pointer(
        vault_book,
        vault_id,
        source_vault,
        governance,
    )
    boa.env.time_travel(seconds=ONE_YEAR // 2)
    expected_recovered_amount = credit_engine.getUserDebtAmount(bob)
    assert credit_engine.updateDebtForUser(
        bob,
        sender=credit_engine.address,
    )
    after_recovery = ledger.userDebt(bob)
    assert after_recovery.amount == expected_recovered_amount
    assert tuple(after_recovery.debtTerms) == stored_terms

    _install_zero_asset_replacement(
        vault_book,
        vault_id,
        governance,
    )
    latest_amount = credit_engine.getUserDebtAmount(bob)
    green_token.transfer(bob, latest_amount, sender=whale)
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    cleared = ledger.userDebt(bob)
    assert cleared.amount == 0


def test_stale_only_update_preserves_rate_during_curve_danger(
    bob,
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    vault_book,
    price_desk,
    mock_curve_prices,
    governance,
):
    _, _, _, stored_terms = _create_stale_only_borrower(
        user=bob,
        asset=alpha_token,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        mock_price_source=mock_price_source,
        teller=teller,
        ledger=ledger,
        vault_book=vault_book,
        governance=governance,
    )
    assert stored_terms[4] == 10_00

    assert price_desk.startAddressUpdateToRegistry(
        2,
        mock_curve_prices,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock())
    assert price_desk.confirmAddressUpdateToRegistry(
        2,
        sender=governance.address,
    )
    mock_curve_prices.setMockGreenPoolData(60_00, 60_00, 250)
    setGeneralDebtConfig(
        _minDynamicRateBoost=0,
        _maxDynamicRateBoost=0,
        _increasePerDangerBlock=40,
    )

    stale_terms = credit_engine.getUserBorrowTerms(bob, True)
    assert stale_terms.highestLtv == 0
    assert stale_terms.debtTerms.borrowRate == 1_00
    assert not credit_engine.updateDebtForUser(
        bob,
        sender=credit_engine.address,
    )
    assert tuple(ledger.userDebt(bob).debtTerms) == stored_terms


def test_stale_only_update_preserves_underscore_discounted_terms(
    bob,
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    vault_book,
    governance,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    credit_engine.setUnderscoreVaultDiscount(
        50_00,
        sender=switchboard_alpha.address,
    )
    _, _, _, stored_terms = _create_stale_only_borrower(
        user=bob,
        asset=alpha_token,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        mock_price_source=mock_price_source,
        teller=teller,
        ledger=ledger,
        vault_book=vault_book,
        governance=governance,
    )
    assert stored_terms[4] == 5_00

    boa.env.time_travel(seconds=ONE_YEAR)
    expected_amount = credit_engine.getUserDebtAmount(bob)
    assert not credit_engine.updateDebtForUser(
        bob,
        sender=credit_engine.address,
    )
    updated = ledger.userDebt(bob)
    assert updated.amount == expected_amount
    assert tuple(updated.debtTerms) == stored_terms


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


def test_claim_loot_preserves_stale_vault_registration(
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
    assert ledger.isParticipatingInVault(bob, vault_id)


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
    assert ledger.isParticipatingInVault(bob, stale_vault_id)
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
    assert ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.isParticipatingInVault(bob, healthy_vault_id)


def test_stale_vault_skip_preserves_all_registrations_without_revert(
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

    num_vaults_before = ledger.numUserVaults(bob)
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.numUserVaults(bob) == num_vaults_before
    assert all(
        ledger.isParticipatingInVault(bob, vault_id)
        for vault_id in vault_ids
    )


def test_claiming_healthy_peer_preserves_stale_points_and_registration(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    teller,
    ledger,
    lootbox,
    ripe_token,
    simple_erc20_vault,
    vault_book,
    governance,
):
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
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

    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
    )
    stale_vault_id = vault_book.getRegId(simple_erc20_vault)
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        stale_vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    assert teller.withdraw(
        alpha_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount

    stale_bundle_before = ledger.getDepositPointsBundle(
        bob,
        stale_vault_id,
        alpha_token,
    )
    assert stale_bundle_before.userPoints.balancePoints > 0
    _install_zero_asset_replacement(
        vault_book,
        stale_vault_id,
        governance,
    )

    healthy_vault_id = _register_vault(
        vault_book,
        governance,
        simple_erc20_vault,
        "healthy reward peer beside stored stale points",
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[healthy_vault_id],
        _stakersPointsAlloc=100,
        _voterPointsAlloc=0,
    )
    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
    )
    boa.env.time_travel(blocks=20)

    num_vaults_before = ledger.numUserVaults(bob)
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable > 0
    assert teller.claimLoot(bob, False, sender=bob) == claimable
    assert ripe_token.balanceOf(bob) == claimable

    stale_bundle_after = ledger.getDepositPointsBundle(
        bob,
        stale_vault_id,
        alpha_token,
    )
    # The returned global aggregate legitimately changes when the healthy peer
    # settles. The stale vault's user- and asset-local point records must not.
    assert stale_bundle_after.userPoints == stale_bundle_before.userPoints
    assert stale_bundle_after.assetPoints == stale_bundle_before.assetPoints
    assert ledger.numUserVaults(bob) == num_vaults_before
    assert ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.isParticipatingInVault(bob, healthy_vault_id)


def test_stale_registration_blocks_capacity_until_pointer_rollback_cleanup(
    bob,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    teller,
    ledger,
    lootbox,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    governance,
):
    max_vaults = 1
    setGeneralConfig(_perUserMaxVaults=max_vaults)
    setAssetConfig(
        alpha_token,
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

    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
    )
    stale_vault_id = vault_book.getRegId(simple_erc20_vault)
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        stale_vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    assert teller.withdraw(
        alpha_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert ledger.getDepositPointsBundle(
        bob,
        stale_vault_id,
        alpha_token,
    ).userPoints.balancePoints > 0

    replacement = _install_settleable_zero_asset_replacement(
        vault_book,
        stale_vault_id,
        governance,
    )
    assert replacement.numUserAssets(bob) == 0
    assert ledger.getNumUserVaults(bob) == max_vaults
    assert ledger.getDepositPointsBundle(
        bob,
        stale_vault_id,
        alpha_token,
    ).userPoints.balancePoints > 0

    target_vault_id = vault_book.getRegId(rebase_erc20_vault)
    assert not ledger.isParticipatingInVault(bob, target_vault_id)
    setAssetConfig(alpha_token, _vaultIds=[target_vault_id])
    with boa.reverts("reached max vaults"):
        performDeposit(
            bob,
            amount,
            alpha_token,
            alpha_token_whale,
            rebase_erc20_vault,
        )

    claimed = lootbox.claimDepositLootForAsset(
        bob,
        stale_vault_id,
        alpha_token,
        sender=teller.address,
    )
    assert claimed > 0
    assert ledger.getDepositPointsBundle(
        bob,
        stale_vault_id,
        alpha_token,
    ).userPoints.balancePoints == 0
    assert ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.getNumUserVaults(bob) == max_vaults

    with boa.reverts("reached max vaults"):
        performDeposit(
            bob,
            amount,
            alpha_token,
            alpha_token_whale,
            rebase_erc20_vault,
        )

    _set_vault_pointer(
        vault_book,
        stale_vault_id,
        simple_erc20_vault,
        governance,
    )
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert not ledger.isParticipatingInVault(bob, stale_vault_id)
    assert ledger.getNumUserVaults(bob) == max_vaults - 1

    performDeposit(
        bob,
        amount,
        alpha_token,
        alpha_token_whale,
        rebase_erc20_vault,
    )
    assert ledger.isParticipatingInVault(bob, target_vault_id)
    assert ledger.getNumUserVaults(bob) == max_vaults


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
