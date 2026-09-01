import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, VAULT_MIGRATOR_HQ_ID
from conf_utils import filter_logs


# vault ids established by the `vault_book` fixture
STAB_POOL_ID = 1
CORE_RIPE_GOV_ID = 2
SIMPLE_VAULT_ID = 3
REBASE_VAULT_ID = 4

DEPOSIT_AMOUNT = 100 * EIGHTEEN_DECIMALS

# mirrors the frozen RipeGov suite's configuration
ASSET_WEIGHT = 100_00
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)


###########
# Helpers #
###########


def _register_vault(source_path, ripe_hq, vault_book, governance, label):
    """Register an additional vault in VaultBook after registry setup has finished."""
    vault = boa.load(source_path, ripe_hq, name=label)
    assert vault_book.startAddNewAddressToRegistry(vault, label, sender=governance.address)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    vault_id = vault_book.confirmNewAddressToRegistry(vault, sender=governance.address)
    assert vault_id != 0
    return vault, vault_id


def _seed_position(teller, vault, token, whale, user, amount=DEPOSIT_AMOUNT):
    """Give `user` a real position in `vault` through the ordinary deposit path."""
    token.transfer(user, amount, sender=whale)
    token.approve(teller.address, amount, sender=user)
    deposited = teller.deposit(token, amount, user, vault, sender=user)
    assert deposited == amount
    return deposited


def _migrate(teller, caller, user, token, source_id, target_id):
    """Migrate every supported source asset for one user through VaultMigrator."""
    hq = boa.load_partial("contracts/registries/RipeHq.vy").at(teller.getRipeHq())
    vault_migrator = boa.load_partial("contracts/core/VaultMigrator.vy").at(
        hq.getAddr(VAULT_MIGRATOR_HQ_ID)
    )
    caller_addr = caller.address if hasattr(caller, "address") else caller
    count = vault_migrator.migrateVaultPositions(
        [user], source_id, target_id, sender=caller_addr
    )
    logs = filter_logs(vault_migrator, "VaultPositionMigrationExecuted")
    assert len(logs) == count
    token_addr = token.address if hasattr(token, "address") else token
    matching = [log for log in logs if log.asset == token_addr]
    return matching[-1].amount if matching else 0


############
# Fixtures #
############


@pytest.fixture
def target_simple_vault(ripe_hq, vault_book, governance):
    return _register_vault(
        "contracts/vaults/SimpleErc20.vy", ripe_hq, vault_book, governance,
        "migration_target_simple_vault",
    )


@pytest.fixture
def target_rebase_vault(ripe_hq, vault_book, governance):
    return _register_vault(
        "contracts/vaults/RebaseErc20.vy", ripe_hq, vault_book, governance,
        "migration_target_rebase_vault",
    )


@pytest.fixture
def target_stab_pool(ripe_hq, vault_book, governance):
    return _register_vault(
        "contracts/vaults/StabilityPool.vy", ripe_hq, vault_book, governance,
        "migration_target_stab_pool",
    )


@pytest.fixture
def noncore_gov_vault(ripe_hq, vault_book, governance):
    """A registered RipeGov vault that is NOT the current core pointer."""
    return _register_vault(
        "contracts/vaults/RipeGov.vy", ripe_hq, vault_book, governance,
        "migration_noncore_gov_vault",
    )


@pytest.fixture
def simple_pair(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale,
    bob, setGeneralConfig, setAssetConfig, switchboard_alpha,
):
    """Bob holds a simple-vault position, both endpoints support the asset, Teller is paused."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)
    return target_vault, target_id


################################
# 7.1 Regression and permissions
################################


def test_migration_rejects_non_switchboard_callers(
    teller, simple_pair, alpha_token, bob, sally, stability_pool, lootbox,
):
    _, target_id = simple_pair

    with boa.reverts("only switchboard allowed"):
        _migrate(teller, sally, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    # a ripe department that is not a switchboard
    with boa.reverts("only switchboard allowed"):
        _migrate(teller, lootbox, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    # a registered vault
    with boa.reverts("only switchboard allowed"):
        _migrate(teller, stability_pool, bob, alpha_token, SIMPLE_VAULT_ID, target_id)


def test_any_registered_switchboard_may_call_vault_migrator(
    teller, simple_pair, alpha_token, bob, switchboard_alpha, switchboard_echo,
    simple_erc20_vault,
):
    """VaultMigrator trusts registered Switchboards; Echo provides the governance ABI."""
    target_vault, target_id = simple_pair
    migrated = _migrate(
        teller, switchboard_alpha, bob, alpha_token, SIMPLE_VAULT_ID, target_id
    )
    assert migrated == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


def test_migration_requires_paused_teller(
    teller, simple_pair, alpha_token, bob, switchboard_echo, switchboard_alpha,
):
    _, target_id = simple_pair
    teller.pause(False, sender=switchboard_alpha.address)
    with boa.reverts("teller not paused"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)


def test_migration_requires_unpaused_endpoints(
    teller, simple_pair, simple_erc20_vault, alpha_token, bob,
    switchboard_echo, switchboard_alpha,
):
    target_vault, target_id = simple_pair

    simple_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("source vault paused"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)
    simple_erc20_vault.pause(False, sender=switchboard_alpha.address)

    target_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("target vault paused"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)


def test_echo_batch_requires_governance(switchboard_echo, simple_pair, alpha_token, bob, sally):
    _, target_id = simple_pair
    with boa.reverts("no perms"):
        switchboard_echo.migrateVaultPositions(
            [bob], SIMPLE_VAULT_ID, target_id, sender=sally
        )


def test_echo_batch_rejects_empty_list(switchboard_echo, simple_pair, governance):
    _, target_id = simple_pair
    with boa.reverts("no migrations"):
        switchboard_echo.migrateVaultPositions(
            [], SIMPLE_VAULT_ID, target_id, sender=governance.address
        )


def test_echo_batch_caps_at_twenty_five_entries(
    switchboard_echo, simple_pair, alpha_token, bob, governance,
):
    """26 entries cannot be encoded at the ABI boundary."""
    _, target_id = simple_pair
    oversized = [bob] * 26
    with pytest.raises(Exception):
        switchboard_echo.migrateVaultPositions(
            oversized, SIMPLE_VAULT_ID, target_id, sender=governance.address
        )


@pytest.mark.parametrize("registered_slots", [20, 21])
def test_normal_migration_capacity_and_explicit_asset_fallback(
    registered_slots, teller, simple_pair, simple_erc20_vault, alpha_token,
    bob, switchboard_echo, governance,
):
    """The batch accepts 20 slots; larger users use the strict explicit path."""
    target, target_id = simple_pair
    simple_erc20_vault.eval(
        f"vaultData.numUserAssets[{bob}] = {registered_slots + 1}"
    )

    if registered_slots == 20:
        assert switchboard_echo.migrateVaultPositions(
            [bob], SIMPLE_VAULT_ID, target_id, sender=governance.address
        ) == 1
    else:
        with boa.reverts("use explicit asset migration"):
            switchboard_echo.migrateVaultPositions(
                [bob], SIMPLE_VAULT_ID, target_id, sender=governance.address
            )
        assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
        assert switchboard_echo.migrateVaultPositionsForUserByAssets(
            bob,
            [alpha_token.address],
            SIMPLE_VAULT_ID,
            target_id,
            sender=governance.address,
        ) == 1

    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert target.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


def test_explicit_asset_migration_rejects_duplicates_before_movement(
    simple_pair, simple_erc20_vault, alpha_token, bob, switchboard_echo,
    governance,
):
    _, target_id = simple_pair
    with boa.reverts("duplicate asset"):
        switchboard_echo.migrateVaultPositionsForUserByAssets(
            bob,
            [alpha_token.address, alpha_token.address],
            SIMPLE_VAULT_ID,
            target_id,
            sender=governance.address,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


def test_explicit_asset_migration_wrapper_validates_authority_and_inputs(
    simple_pair, alpha_token, bob, sally, switchboard_echo, governance,
):
    _, target_id = simple_pair
    with boa.reverts("no perms"):
        switchboard_echo.migrateVaultPositionsForUserByAssets(
            bob, [alpha_token.address], SIMPLE_VAULT_ID, target_id, sender=sally
        )
    with boa.reverts("no migrations"):
        switchboard_echo.migrateVaultPositionsForUserByAssets(
            bob, [], SIMPLE_VAULT_ID, target_id, sender=governance.address
        )


@pytest.mark.parametrize(
    ("invalid_case", "expected_revert"),
    [
        ("zero", "invalid asset"),
        ("missing", "no source position"),
        ("unsupported", "unsupported target asset"),
    ],
)
def test_explicit_asset_migration_validates_full_list_before_movement(
    invalid_case,
    expected_revert,
    teller,
    simple_pair,
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    bob,
    switchboard_alpha,
    switchboard_echo,
    governance,
    setAssetConfig,
):
    target, target_id = simple_pair
    invalid_asset = ZERO_ADDRESS if invalid_case == "zero" else bravo_token.address

    if invalid_case == "unsupported":
        setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID])
        teller.pause(False, sender=switchboard_alpha.address)
        _seed_position(
            teller,
            simple_erc20_vault,
            bravo_token,
            bravo_token_whale,
            bob,
        )
        teller.pause(True, sender=switchboard_alpha.address)

    with boa.reverts(expected_revert):
        switchboard_echo.migrateVaultPositionsForUserByAssets(
            bob,
            [alpha_token.address, invalid_asset],
            SIMPLE_VAULT_ID,
            target_id,
            sender=governance.address,
        )

    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    assert target.getTotalAmountForUser(bob, alpha_token) == 0
    if invalid_case == "unsupported":
        assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == DEPOSIT_AMOUNT
        assert target.getTotalAmountForUser(bob, bravo_token) == 0
    assert filter_logs(switchboard_echo, "VaultPositionMigrationExecuted") == []


def test_generic_user_with_twenty_one_real_assets_completes_explicit_twenty_plus_one(
    target_simple_vault,
    governance,
    simple_erc20_vault,
    bob,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_simple_vault
    setGeneralConfig()
    amount = EIGHTEEN_DECIMALS
    assets = []
    for i in range(21):
        asset = boa.load(
            "contracts/mock/MockErc20.vy",
            governance.address,
            f"Migration Generic {i}",
            f"MG{i}",
            18,
            0,
            name=f"migration_generic_{i}",
        )
        setAssetConfig(asset, _vaultIds=[SIMPLE_VAULT_ID, target_id])
        asset.mint(simple_erc20_vault, amount, sender=governance.address)
        assert simple_erc20_vault.depositTokensInVault(
            bob, asset, amount, sender=teller.address
        ) == amount
        assets.append(asset)

    ledger.addVaultToUser(bob, SIMPLE_VAULT_ID, sender=teller.address)
    assert simple_erc20_vault.numUserAssets(bob) == 22
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    teller.pause(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)

    with boa.reverts("use explicit asset migration"):
        switchboard_echo.migrateVaultPositions(
            [bob], SIMPLE_VAULT_ID, target_id, sender=governance.address
        )
    for asset in assets:
        assert simple_erc20_vault.getTotalAmountForUser(bob, asset) == amount
        assert target.getTotalAmountForUser(bob, asset) == 0

    assert switchboard_echo.migrateVaultPositionsForUserByAssets(
        bob,
        [asset.address for asset in assets[:20]],
        SIMPLE_VAULT_ID,
        target_id,
        sender=governance.address,
    ) == 20
    first_action_block = ledger.lastTouch(bob)
    assert len(filter_logs(
        switchboard_echo, "VaultPositionMigrationExecuted"
    )) == 20

    boa.env.time_travel(blocks=1)
    assert switchboard_echo.migrateVaultPositionsForUserByAssets(
        bob,
        [assets[20].address],
        SIMPLE_VAULT_ID,
        target_id,
        sender=governance.address,
    ) == 1
    assert ledger.lastTouch(bob) > first_action_block
    assert len(filter_logs(
        switchboard_echo, "VaultPositionMigrationExecuted"
    )) == 1

    for asset in assets:
        assert simple_erc20_vault.getTotalAmountForUser(bob, asset) == 0
        assert target.getTotalAmountForUser(bob, asset) == amount
        source_points = ledger.getDepositPointsBundle(
            bob, SIMPLE_VAULT_ID, asset
        ).userPoints
        target_points = ledger.getDepositPointsBundle(
            bob, target_id, asset
        ).userPoints
        assert source_points.lastBalance == 0
        assert source_points.lastUpdate != 0
        assert target_points.lastBalance > 0
        assert target_points.lastUpdate != 0


def test_teller_migration_steps_are_vault_migrator_only(
    teller, simple_pair, simple_erc20_vault, alpha_token, bob, switchboard_echo,
):
    target_vault, target_id = simple_pair
    with boa.reverts("only vault migrator allowed"):
        teller.withdrawOnVaultMigration(
            bob, alpha_token, simple_erc20_vault, sender=switchboard_echo.address
        )
    with boa.reverts("only vault migrator allowed"):
        teller.depositOnVaultMigration(
            bob,
            alpha_token,
            DEPOSIT_AMOUNT,
            target_id,
            target_vault,
            sender=switchboard_echo.address,
        )


######################
# 7.2 Endpoint policy
######################


def test_zero_user_is_skipped_and_degenerate_routes_fail(
    teller, simple_pair, alpha_token, bob, switchboard_echo,
):
    _, target_id = simple_pair

    assert _migrate(
        teller, switchboard_echo, ZERO_ADDRESS, alpha_token, SIMPLE_VAULT_ID, target_id
    ) == 0

    with boa.reverts("invalid vault id"):
        _migrate(teller, switchboard_echo, bob, alpha_token, 0, target_id)

    with boa.reverts("invalid vault id"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, 0)

    with boa.reverts("same vault"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, SIMPLE_VAULT_ID)


def test_unregistered_vault_ids_fail(teller, simple_pair, alpha_token, bob, switchboard_echo):
    _, target_id = simple_pair
    with boa.reverts("invalid source vault id"):
        _migrate(teller, switchboard_echo, bob, alpha_token, 999, target_id)
    with boa.reverts("invalid target vault id"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, 999)


def test_unsupported_target_asset_is_skipped_and_left_in_source(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo,
):
    _, target_id = target_simple_vault
    setGeneralConfig()

    # only the source supports the asset
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)
    assert _migrate(
        teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id
    ) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT

    # A live source position remains enumerable even if current configuration no
    # longer lists that source vault. Target support is the migration gate.
    setAssetConfig(alpha_token, _vaultIds=[target_id])
    assert _migrate(
        teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id
    ) == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


def test_user_without_source_positions_is_a_noop(
    teller, simple_pair, alpha_token, sally, switchboard_echo,
):
    """A user with no source assets is skipped without housekeeping or events."""
    _, target_id = simple_pair
    assert _migrate(
        teller, switchboard_echo, sally, alpha_token, SIMPLE_VAULT_ID, target_id
    ) == 0


def test_core_ripe_gov_id_rejected_as_target(
    teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, mission_control,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, CORE_RIPE_GOV_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    assert mission_control.coreRipeGovVaultId() == CORE_RIPE_GOV_ID
    with boa.reverts("target is ripe gov"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, CORE_RIPE_GOV_ID)


def test_core_ripe_gov_id_rejected_as_source(
    teller, ripe_gov_vault, target_simple_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, mission_control,
):
    """Bob holds a real core-RipeGov position, so the source-Ledger check passes and the
    core-pointer exclusion is the assertion actually under test."""
    _, target_id = target_simple_vault
    setGeneralConfig()
    mission_control.setRipeGovVaultConfig(
        alpha_token, ASSET_WEIGHT, False, LOCK_TERMS, sender=switchboard_alpha.address
    )
    setAssetConfig(alpha_token, _vaultIds=[CORE_RIPE_GOV_ID, target_id])

    alpha_token.transfer(bob, DEPOSIT_AMOUNT, sender=alpha_token_whale)
    alpha_token.approve(teller.address, DEPOSIT_AMOUNT, sender=bob)
    teller.depositIntoGovVault(alpha_token, DEPOSIT_AMOUNT, 0, bob, sender=bob)
    assert ripe_gov_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT

    teller.pause(True, sender=switchboard_alpha.address)
    assert mission_control.coreRipeGovVaultId() == CORE_RIPE_GOV_ID
    with boa.reverts("source is ripe gov"):
        _migrate(teller, switchboard_echo, bob, alpha_token, CORE_RIPE_GOV_ID, target_id)


def test_core_pointer_rotation_preserves_the_historical_exclusion_boundary(
    teller, simple_erc20_vault, ripe_gov_vault, target_simple_vault, alpha_token,
    alpha_token_whale, bob, setGeneralConfig, setAssetConfig, switchboard_alpha,
    switchboard_echo, mission_control,
):
    """Every current or historical core RipeGov stays out of the generic path."""
    _, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id, CORE_RIPE_GOV_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    # before rotation, id 2 is classified as RipeGov
    with boa.reverts("target is ripe gov"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, CORE_RIPE_GOV_ID)

    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)
    assert mission_control.coreRipeGovVaultId() == target_id

    # the NEW core id is rejected immediately
    with boa.reverts("target is ripe gov"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    # The previous core id remains classified even after rotation. Classification
    # runs before endpoint pause checks, so it is the deterministic rejection.
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("target is ripe gov"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, CORE_RIPE_GOV_ID)


def test_paused_noncore_ripe_gov_still_fails_generic_path(
    teller, simple_erc20_vault, noncore_gov_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo,
):
    """A non-core RipeGov can exist, but the generic path requires unpaused endpoints."""
    gov_vault, gov_id = noncore_gov_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, gov_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    gov_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("target vault paused"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, gov_id)


def test_ordinary_to_stability_is_rejected(
    teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, mission_control,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, STAB_POOL_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    assert mission_control.isStabVaultId(STAB_POOL_ID)
    assert not mission_control.isStabVaultId(SIMPLE_VAULT_ID)

    with boa.reverts("stab vault mismatch"):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, STAB_POOL_ID)


def test_stability_to_ordinary_is_rejected(
    teller, stability_pool, green_token, savings_green, whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, mission_control,
):
    """Bob holds a real stability position, so the source-Ledger check passes and the
    classification rule is the assertion actually under test."""
    setGeneralConfig()
    setAssetConfig(savings_green, _vaultIds=[STAB_POOL_ID, SIMPLE_VAULT_ID])

    green_token.transfer(bob, DEPOSIT_AMOUNT, sender=whale)
    green_token.approve(teller.address, DEPOSIT_AMOUNT, sender=bob)
    sgreen = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, DEPOSIT_AMOUNT, sender=bob)
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == sgreen

    teller.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("stab vault mismatch"):
        _migrate(teller, switchboard_echo, bob, savings_green, STAB_POOL_ID, SIMPLE_VAULT_ID)


def test_simple_to_rebase_is_allowed(
    teller, simple_erc20_vault, rebase_erc20_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo,
):
    """Both endpoints are collateral-bearing and the same token amount moves."""
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, REBASE_VAULT_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, REBASE_VAULT_ID)
    assert migrated == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert abs(rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) - DEPOSIT_AMOUNT) <= 1
    assert alpha_token.balanceOf(rebase_erc20_vault) == DEPOSIT_AMOUNT


def test_rebase_to_simple_is_allowed(
    teller, simple_erc20_vault, rebase_erc20_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, REBASE_VAULT_ID])
    _seed_position(teller, rebase_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, REBASE_VAULT_ID, SIMPLE_VAULT_ID)
    assert migrated == DEPOSIT_AMOUNT
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


###################################
# 7.3 Value, custody and rollback
###################################


def test_simple_to_simple_preserves_exact_amount(
    teller, simple_pair, simple_erc20_vault, alpha_token, bob, switchboard_echo,
):
    target_vault, target_id = simple_pair
    source_before = alpha_token.balanceOf(simple_erc20_vault)

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert migrated == DEPOSIT_AMOUNT
    assert alpha_token.balanceOf(simple_erc20_vault) == source_before - DEPOSIT_AMOUNT
    assert alpha_token.balanceOf(target_vault) == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


def test_rebase_to_rebase_preserves_exact_token_amount(
    teller, rebase_erc20_vault, target_rebase_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo,
):
    target_vault, target_id = target_rebase_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[REBASE_VAULT_ID, target_id])
    _seed_position(teller, rebase_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, REBASE_VAULT_ID, target_id)

    # the exact token amount moves; share-derived value carries a 1-wei rounding bound
    assert migrated == DEPOSIT_AMOUNT
    assert alpha_token.balanceOf(target_vault) == DEPOSIT_AMOUNT
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert abs(target_vault.getTotalAmountForUser(bob, alpha_token) - DEPOSIT_AMOUNT) <= 1


def test_stability_pool_to_stability_pool(
    teller, stability_pool, target_stab_pool, green_token, savings_green, whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, mission_control,
):
    """Stability positions migrate within explicit share/value rounding bounds."""
    stab_vault, stab_id = target_stab_pool
    setGeneralConfig()
    setAssetConfig(savings_green, _vaultIds=[STAB_POOL_ID, stab_id])

    # deposit first, while the ORIGINAL pool is still the preferred pointer
    green_token.transfer(bob, DEPOSIT_AMOUNT, sender=whale)
    green_token.approve(teller.address, DEPOSIT_AMOUNT, sender=bob)
    sgreen = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, DEPOSIT_AMOUNT, sender=bob)
    assert sgreen > 0
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == sgreen

    # now mark the new pool as a stability vault so classification matches
    mission_control.setPreferredStabVaultId(stab_id, sender=switchboard_alpha.address)
    assert mission_control.isStabVaultId(STAB_POOL_ID)
    assert mission_control.isStabVaultId(stab_id)

    teller.pause(True, sender=switchboard_alpha.address)
    migrated = _migrate(teller, switchboard_echo, bob, savings_green, STAB_POOL_ID, stab_id)

    assert migrated == sgreen
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == 0
    assert abs(stab_vault.getTotalAmountForUser(bob, savings_green) - sgreen) <= 1
    assert savings_green.balanceOf(stab_vault) == sgreen


def test_teller_retains_nothing_and_creates_no_allowance(
    teller, simple_pair, alpha_token, bob, switchboard_echo, simple_erc20_vault,
):
    target_vault, target_id = simple_pair
    assert alpha_token.balanceOf(teller) == 0

    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert alpha_token.balanceOf(teller) == 0
    assert alpha_token.allowance(teller.address, target_vault.address) == 0
    assert alpha_token.allowance(teller.address, simple_erc20_vault.address) == 0


def test_prefunded_teller_balance_is_preserved_and_cannot_subsidize(
    teller, simple_pair, alpha_token, alpha_token_whale, bob, switchboard_echo,
):
    """A stray Teller balance must survive the migration exactly."""
    target_vault, target_id = simple_pair
    stray = 7 * EIGHTEEN_DECIMALS
    alpha_token.transfer(teller, stray, sender=alpha_token_whale)
    assert alpha_token.balanceOf(teller) == stray

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert migrated == DEPOSIT_AMOUNT
    assert alpha_token.balanceOf(teller) == stray
    assert alpha_token.balanceOf(target_vault) == DEPOSIT_AMOUNT


def test_replay_of_successful_migration_is_a_noop(
    teller, simple_pair, alpha_token, bob, switchboard_echo,
):
    """A replay sees no live source balance and performs no second migration."""
    _, target_id = simple_pair
    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)
    assert _migrate(
        teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id
    ) == 0


def test_failed_entry_rolls_back_the_whole_echo_batch(
    teller, simple_erc20_vault, target_simple_vault, alpha_token,
    alpha_token_whale, bravo_token, bravo_token_whale, bob, sally,
    setGeneralConfig, setGeneralDebtConfig, setAssetConfig, mock_price_source,
    switchboard_alpha, switchboard_echo, governance, ledger,
):
    """A later-user failure restores complete pre-call state for every earlier entry."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setGeneralDebtConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, bravo_token, bravo_token_whale, sally)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    teller.borrow(40 * EIGHTEEN_DECIMALS, sally, False, sender=sally)
    mock_price_source.setPrice(bravo_token, 0)
    teller.pause(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)

    source_before = alpha_token.balanceOf(simple_erc20_vault)
    target_before = alpha_token.balanceOf(target_vault)
    bob_before = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert bob_before == DEPOSIT_AMOUNT

    # Bob migrates first. Sally's later housekeeping fails debt health after her
    # collateral loses its price, reverting both users atomically.
    with pytest.raises(BoaError):
        switchboard_echo.migrateVaultPositions(
            [bob, sally], SIMPLE_VAULT_ID, target_id,
            sender=governance.address,
        )

    assert alpha_token.balanceOf(simple_erc20_vault) == source_before
    assert alpha_token.balanceOf(target_vault) == target_before
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == bob_before
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(sally, bravo_token) == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(sally, bravo_token) == 0
    assert not ledger.getDepositLedgerData(bob, target_id).isParticipatingInVault
    assert filter_logs(switchboard_echo, "VaultPositionMigrationExecuted") == []


def test_batch_migrates_several_users_atomically(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale,
    bob, sally, setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, governance,
):
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, sally)
    teller.pause(True, sender=switchboard_alpha.address)

    count = switchboard_echo.migrateVaultPositions(
        [bob, sally], SIMPLE_VAULT_ID, target_id,
        sender=governance.address,
    )
    assert count == 2
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(sally, alpha_token) == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(sally, alpha_token) == 0


def test_all_user_assets_migrate_with_one_housekeeping_call(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale,
    bravo_token, bravo_token_whale, bob, setGeneralConfig, setAssetConfig,
    switchboard_alpha, switchboard_echo, governance, mission_control,
):
    """All supported assets move before one per-user higher-risk housekeeping call."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, bravo_token, bravo_token_whale, bob)

    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    teller.pause(True, sender=switchboard_alpha.address)

    # the seeding deposits stamped bob's last touch in this block; move past them
    boa.env.time_travel(blocks=1)

    assert switchboard_echo.migrateVaultPositions(
        [bob], SIMPLE_VAULT_ID, target_id,
        sender=governance.address,
    ) == 2
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(bob, bravo_token) == DEPOSIT_AMOUNT


def test_duplicate_user_is_harmless_after_first_entry_migrates_all_assets(
    teller, simple_pair, alpha_token, bob, switchboard_echo, governance,
):
    """A duplicate manifest user is a no-op after that user's first full migration."""
    target_vault, target_id = simple_pair
    assert switchboard_echo.migrateVaultPositions(
        [bob, bob], SIMPLE_VAULT_ID, target_id, sender=governance.address
    ) == 1
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT


#####################################
# 7.4 Ledger, Lootbox and debt health
#####################################


def test_target_ledger_participation_added_once(
    teller, simple_pair, alpha_token, bob, switchboard_echo, ledger,
):
    _, target_id = simple_pair

    assert ledger.getDepositLedgerData(bob, SIMPLE_VAULT_ID).isParticipatingInVault
    assert not ledger.getDepositLedgerData(bob, target_id).isParticipatingInVault
    vaults_before = ledger.getNumUserVaults(bob)

    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert ledger.getDepositLedgerData(bob, target_id).isParticipatingInVault
    assert ledger.getNumUserVaults(bob) == vaults_before + 1


def test_source_participation_survives_for_a_second_asset(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale,
    bravo_token, bravo_token_whale, bob, setGeneralConfig, setAssetConfig,
    switchboard_alpha, switchboard_echo, ledger,
):
    """Migrating one asset must not strip participation another asset still needs."""
    _, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, bravo_token, bravo_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert ledger.getDepositLedgerData(bob, SIMPLE_VAULT_ID).isParticipatingInVault
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == DEPOSIT_AMOUNT
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


def test_normal_claim_cleans_source_only_after_all_assets_migrate(
    teller, simple_erc20_vault, target_simple_vault, alpha_token,
    alpha_token_whale, bravo_token, bravo_token_whale, bob, setGeneralConfig,
    setAssetConfig, setRipeRewardsConfig, switchboard_alpha, switchboard_echo,
    ledger, ripe_token,
):
    """Ordinary Lootbox cleanup handles a source with multiple migrated assets."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID])
    setRipeRewardsConfig(_autoStakeRatio=0, _autoStakeDurationRatio=0)
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, bravo_token, bravo_token_whale, bob)
    boa.env.time_travel(blocks=20)
    teller.pause(True, sender=switchboard_alpha.address)

    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)
    assert ledger.isParticipatingInVault(bob, SIMPLE_VAULT_ID)
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert simple_erc20_vault.doesUserHaveBalance(bob, bravo_token)

    # A normal claim may clean the depleted asset, but the second live asset keeps the
    # source vault in Ledger.
    teller.pause(False, sender=switchboard_alpha.address)
    teller.claimLoot(bob, False, sender=bob)
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert ledger.isParticipatingInVault(bob, SIMPLE_VAULT_ID)

    boa.env.time_travel(blocks=1)
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    teller.pause(True, sender=switchboard_alpha.address)
    _migrate(teller, switchboard_echo, bob, bravo_token, SIMPLE_VAULT_ID, target_id)
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert ledger.isParticipatingInVault(bob, SIMPLE_VAULT_ID)

    # Only after the final asset is gone does the next ordinary claim remove the
    # remaining source registration and source Ledger entry.
    teller.pause(False, sender=switchboard_alpha.address)
    ripe_before = ripe_token.balanceOf(bob)
    claimed = teller.claimLoot(bob, False, sender=bob)
    assert ripe_token.balanceOf(bob) == ripe_before + claimed
    assert not simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert not ledger.isParticipatingInVault(bob, SIMPLE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(bob, bravo_token) == DEPOSIT_AMOUNT


def test_untouched_source_assets_are_unchanged(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale,
    bravo_token, bravo_token_whale, bob, setGeneralConfig, setAssetConfig,
    switchboard_alpha, switchboard_echo,
):
    _, target_id = target_simple_vault
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    setAssetConfig(bravo_token, _vaultIds=[SIMPLE_VAULT_ID])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    _seed_position(teller, simple_erc20_vault, bravo_token, bravo_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    bravo_vault_before = bravo_token.balanceOf(simple_erc20_vault)
    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)
    assert bravo_token.balanceOf(simple_erc20_vault) == bravo_vault_before


def test_user_at_vault_limit_can_migrate(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setAssetConfig, switchboard_alpha, switchboard_echo, ledger,
):
    """The trusted-caller path bypasses the per-user vault cap, so a user at the limit
    can still be migrated. Source participation stays enumerable until ordinary cleanup."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig(_perUserMaxVaults=1)
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    teller.pause(True, sender=switchboard_alpha.address)

    assert ledger.getNumUserVaults(bob) == 1
    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert migrated == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    # temporary enumeration: both vaults remain listed until Lootbox cleanup runs
    assert ledger.getNumUserVaults(bob) == 2


def test_source_deposit_points_are_checkpointed(
    teller, simple_pair, simple_erc20_vault, alpha_token, bob, switchboard_echo, lootbox,
):
    _, target_id = simple_pair
    boa.env.time_travel(blocks=50)

    _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    # the source position is settled through this block at a zero current balance
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


##############
# 7.5 Events
##############


def test_migration_emits_withdrawal_deposit_and_echo_events(
    teller, simple_pair, simple_erc20_vault, alpha_token, bob, switchboard_echo, governance,
):
    target_vault, target_id = simple_pair

    switchboard_echo.migrateVaultPositions(
        [bob], SIMPLE_VAULT_ID, target_id,
        sender=governance.address,
    )

    # Echo was the entry point, so the whole transaction's logs decode off it.
    # The source withdrawal event comes from the vault itself: migrateVaultPosition calls
    # withdrawTokensFromVault directly rather than through Teller's _withdraw, so no
    # TellerWithdrawal is emitted. The audit trail is vault withdrawal + TellerDeposit + Echo.
    assert filter_logs(switchboard_echo, "TellerWithdrawal") == []

    withdrawals = filter_logs(switchboard_echo, "SimpleErc20VaultWithdrawal")
    assert len(withdrawals) == 1
    assert withdrawals[0].user == bob
    assert withdrawals[0].asset == alpha_token.address
    assert withdrawals[0].amount == DEPOSIT_AMOUNT
    assert withdrawals[0].isDepleted

    deposits = filter_logs(switchboard_echo, "TellerDeposit")
    assert len(deposits) == 1
    assert deposits[0].user == bob
    assert deposits[0].amount == DEPOSIT_AMOUNT
    assert deposits[0].vaultAddr == target_vault.address
    assert deposits[0].vaultId == target_id

    echo_logs = filter_logs(switchboard_echo, "VaultPositionMigrationExecuted")
    assert len(echo_logs) == 1
    log = echo_logs[0]
    assert log.user == bob
    assert log.asset == alpha_token.address
    assert log.sourceVaultId == SIMPLE_VAULT_ID
    assert log.targetVaultId == target_id
    assert log.amount == DEPOSIT_AMOUNT


######################
# Debt health (7.4)
######################


def test_healthy_indebted_user_migrates_and_stays_healthy(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setGeneralDebtConfig, setAssetConfig, mock_price_source,
    switchboard_alpha, switchboard_echo, credit_engine, ledger,
):
    """Collateral moves between two ordinary vaults, so debt health is unchanged and the
    final higher-risk housekeeping assertion passes."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setGeneralDebtConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    collateral_before = credit_engine.getCollateralValue(bob)
    assert collateral_before != 0

    teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    debt_before = ledger.userDebt(bob).amount
    assert debt_before != 0

    teller.pause(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)

    migrated = _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    assert migrated == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    # collateral value is carried across, so the user remains healthy and the final
    # higher-risk housekeeping assertion passes rather than reverting
    assert credit_engine.getCollateralValue(bob) == collateral_before
    # debt only moves by accrued interest over the elapsed block, never by the migration
    debt_after = ledger.userDebt(bob).amount
    assert debt_after >= debt_before
    assert debt_after - debt_before < debt_before // 1000


def test_migration_reverts_when_target_is_not_valid_collateral(
    teller, simple_erc20_vault, target_simple_vault, alpha_token, alpha_token_whale, bob,
    setGeneralConfig, setGeneralDebtConfig, setAssetConfig, createDebtTerms,
    mock_price_source, switchboard_alpha, switchboard_echo,
):
    """If the target vault cannot carry the collateral value, the final debt-health
    assertion in housekeeping reverts the whole migration atomically."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig()
    setGeneralDebtConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    teller.borrow(40 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # drop the asset's LTV to zero only in the target vault by removing it from the
    # target's supported set is not possible post-validation, so instead crash the price
    mock_price_source.setPrice(alpha_token, 0)

    teller.pause(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)

    with pytest.raises(BoaError):
        _migrate(teller, switchboard_echo, bob, alpha_token, SIMPLE_VAULT_ID, target_id)

    # complete rollback
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == DEPOSIT_AMOUNT
    assert target_vault.getTotalAmountForUser(bob, alpha_token) == 0


##################
# Gas (7.5)
##################


@pytest.mark.gas
@pytest.mark.parametrize("num_users", [1, 5, 10, 25])
def test_migration_batch_gas(
    num_users, teller, simple_erc20_vault, target_simple_vault, alpha_token,
    alpha_token_whale, setGeneralConfig, setAssetConfig, switchboard_alpha,
    switchboard_echo, governance, env,
):
    """Records gas for the production batch sizes. Only the one-user case is a design
    blocker; larger batches inform the runbook's batch-size choice."""
    target_vault, target_id = target_simple_vault
    setGeneralConfig(_perUserMaxVaults=5)
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID, target_id])

    users = [boa.env.generate_address() for _ in range(num_users)]
    for user in users:
        _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, user)

    teller.pause(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)

    count = switchboard_echo.migrateVaultPositions(
        users, SIMPLE_VAULT_ID, target_id, sender=governance.address
    )
    gas_used = switchboard_echo._computation.get_gas_used()

    assert count == num_users
    for user in users:
        assert target_vault.getTotalAmountForUser(user, alpha_token) == DEPOSIT_AMOUNT

    print(
        f"MIGRATION_GAS users={num_users} total={gas_used} per_user={gas_used // num_users}"
    )
    # a single migration must fit comfortably inside any plausible block envelope
    assert gas_used < 30_000_000


###############################################
# Teller-side backup guards (defence in depth)
###############################################


MALICIOUS_TELLER_UTILS = """
# @version 0.4.3

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

struct Addys:
    hq: address
    greenToken: address
    savingsGreen: address
    ripeToken: address
    ledger: address
    missionControl: address
    switchboard: address
    priceDesk: address
    vaultBook: address
    auctionHouse: address
    auctionHouseNft: address
    boardroom: address
    bondRoom: address
    creditEngine: address
    endaoment: address
    humanResources: address
    lootbox: address
    teller: address

attackerVault: public(address)

@deploy
def __init__(_attackerVault: address):
    self.attackerVault = _attackerVault

@view
@external
def getVaultAddrAndId(
    _asset: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _vaultBook: address,
    _missionControl: address,
) -> (address, uint256):
    # a compromised TellerUtils names an address that is NOT a registered vault
    return self.attackerVault, _vaultId
"""


def test_deposit_rejects_a_vault_address_not_registered_in_vaultbook(
    teller, ripe_hq, simple_erc20_vault, alpha_token, alpha_token_whale, bob, sally,
    setGeneralConfig, setAssetConfig, governance,
):
    """Teller's backup guard: `_deposit` re-validates the TellerUtils-supplied vault address
    against Teller's own VaultBook, so a compromised TellerUtils cannot redirect funds out of
    the protocol. Proven by actually repointing RipeHq's TellerUtils slot at a hostile stub."""
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[SIMPLE_VAULT_ID])

    # sanity: the honest path works
    _seed_position(teller, simple_erc20_vault, alpha_token, alpha_token_whale, bob)

    TELLER_UTILS_REG_ID = 20
    hostile = boa.loads(MALICIOUS_TELLER_UTILS, sally, name="hostile_teller_utils")

    ripe_hq.startAddressUpdateToRegistry(
        TELLER_UTILS_REG_ID, hostile, sender=governance.address
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        TELLER_UTILS_REG_ID, sender=governance.address
    )

    # the hostile stub names `sally` (an EOA, not a registered vault) as the deposit target
    alpha_token.transfer(bob, DEPOSIT_AMOUNT, sender=alpha_token_whale)
    alpha_token.approve(teller.address, DEPOSIT_AMOUNT, sender=bob)
    sally_before = alpha_token.balanceOf(sally)

    with boa.reverts("invalid vault"):
        teller.deposit(alpha_token, DEPOSIT_AMOUNT, bob, simple_erc20_vault, sender=bob)

    # no funds left the protocol
    assert alpha_token.balanceOf(sally) == sally_before
