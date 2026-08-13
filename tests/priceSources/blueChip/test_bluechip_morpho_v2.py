import boa
import pytest

from config.BluePrint import PARAMS
from constants import (
    BLUE_CHIP_PROTOCOL_EULER,
    BLUE_CHIP_PROTOCOL_FLUID,
    BLUE_CHIP_PROTOCOL_MORPHO,
    BLUE_CHIP_PROTOCOL_MORPHO_V2,
    EIGHTEEN_DECIMALS,
    MAX_UINT256,
    ZERO_ADDRESS,
)


# Deployment-owned launch identities. This prerequisite adds the constructor
# seam and protocol behavior only; it does not mutate deployment configuration.
STEAKHOUSE_USDG_VAULT = "0xBeEff033F34C046626B8D0A041844C5d1A5409dd"
ROBINHOOD_MORPHO_V2_FACTORY = "0x0FBad98595b0186dA120E41f77C102beb49f803c"


@pytest.fixture
def morpho_v2_factory():
    return boa.load(
        "contracts/mock/MockMorphoV2Factory.vy",
        name="morpho_v2_factory",
    )


@pytest.fixture
def morpho_v2_vault(alpha_token):
    return boa.load(
        "contracts/mock/MockMorphoV2Vault.vy",
        alpha_token,
        18,
        100 * EIGHTEEN_DECIMALS,
        125 * EIGHTEEN_DECIMALS // 100,
        name="morpho_v2_vault",
    )


@pytest.fixture
def deploy_blue_chip_morpho_v2(
    ripe_hq_deploy,
    governance,
    mock_yield_registry,
):
    def _deploy(factory):
        c = boa.load(
            "contracts/priceSources/BlueChipYieldPrices.vy",
            ripe_hq_deploy,
            ZERO_ADDRESS,
            PARAMS["local"]["PRICE_DESK_MIN_REG_TIMELOCK"],
            PARAMS["local"]["PRICE_DESK_MAX_REG_TIMELOCK"],
            [mock_yield_registry, mock_yield_registry],
            [mock_yield_registry, mock_yield_registry],
            mock_yield_registry,
            mock_yield_registry,
            mock_yield_registry,
            mock_yield_registry,
            factory,
            name="blue_chip_morpho_v2",
        )
        assert c.setActionTimeLockAfterSetup(sender=governance.address)
        return c

    return _deploy


@pytest.fixture
def morpho_v2_prices(deploy_blue_chip_morpho_v2, morpho_v2_factory):
    return deploy_blue_chip_morpho_v2(morpho_v2_factory)


def _is_valid(prices, vault):
    return prices.isValidNewFeed(
        vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        5,
        0,
        100,
    )


def _register(
    prices,
    factory,
    vault,
    underlying,
    price_source,
    governance,
    *,
    underlying_price=EIGHTEEN_DECIMALS,
    max_snapshots=5,
    max_upside=0,
):
    factory.setVault(vault, True)
    price_source.setPrice(underlying, underlying_price)
    assert prices.addNewPriceFeed(
        vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        max_snapshots,
        max_upside,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=prices.actionTimeLock() + 1)
    assert prices.confirmNewPriceFeed(vault, sender=governance.address)


def test_selected_launch_identity_binds_constructor_and_fails_closed_offline(
    deploy_blue_chip_morpho_v2,
):
    prices = deploy_blue_chip_morpho_v2(ROBINHOOD_MORPHO_V2_FACTORY)

    assert prices.MORPHO_V2_ADDR() == ROBINHOOD_MORPHO_V2_FACTORY
    # There is intentionally no RPC/code overlay in this test environment.
    assert not _is_valid(prices, STEAKHOUSE_USDG_VAULT)


def test_supported_morpho_v2_vault_is_recognized_and_priced(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)

    assert morpho_v2_prices.MORPHO_V2_ADDR() == morpho_v2_factory.address
    assert _is_valid(morpho_v2_prices, morpho_v2_vault)
    assert morpho_v2_prices.addNewPriceFeed(
        morpho_v2_vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        5,
        0,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=morpho_v2_prices.actionTimeLock() + 1)
    assert morpho_v2_prices.confirmNewPriceFeed(
        morpho_v2_vault,
        sender=governance.address,
    )

    config = morpho_v2_prices.priceConfigs(morpho_v2_vault)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO_V2
    assert config.underlyingAsset == alpha_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 18
    assert config.lastSnapshot.totalSupply == 100
    assert config.lastSnapshot.pricePerShare == 125 * EIGHTEEN_DECIMALS // 100
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 5 * EIGHTEEN_DECIMALS // 2

    # Current downside remains authoritative for the new ERC-4626 lane.
    morpho_v2_vault.setPricePerShare(EIGHTEEN_DECIMALS)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 2 * EIGHTEEN_DECIMALS


def test_unlisted_or_incompatible_vaults_fail_closed(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    deploy3r,
):
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)

    # Even an EOA explicitly listed by a factory cannot satisfy asset().
    morpho_v2_factory.setVault(deploy3r, True)
    assert not _is_valid(morpho_v2_prices, deploy3r)


def test_zero_or_eoa_factory_fails_closed(
    deploy_blue_chip_morpho_v2,
    morpho_v2_vault,
    deploy3r,
):
    assert not _is_valid(deploy_blue_chip_morpho_v2(ZERO_ADDRESS), morpho_v2_vault)
    assert not _is_valid(deploy_blue_chip_morpho_v2(deploy3r), morpho_v2_vault)


@pytest.mark.parametrize("mode", [1, 2, 3, 4, 5])
def test_factory_revert_or_malformed_return_fails_closed(
    mode,
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    morpho_v2_factory.setResponseMode(mode)
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)


@pytest.mark.parametrize(
    ("modes", "expected_modes"),
    [
        ((1, 0, 0, 0), range(1, 6)),
        ((0, 1, 0, 0), range(1, 6)),
        ((0, 0, 1, 0), range(1, 6)),
        ((0, 0, 0, 1), range(1, 6)),
    ],
)
def test_vault_revert_or_malformed_return_fails_closed(
    modes,
    expected_modes,
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    for mode in expected_modes:
        selected = tuple(mode if value else 0 for value in modes)
        morpho_v2_vault.setModes(*selected)
        assert not _is_valid(morpho_v2_prices, morpho_v2_vault)


@pytest.mark.parametrize("convert_mode", [1, 2, 3, 4, 5])
def test_registered_vault_malformed_conversion_returns_zero_price(
    convert_mode,
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    morpho_v2_prices.addNewPriceFeed(
        morpho_v2_vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        5,
        0,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=morpho_v2_prices.actionTimeLock() + 1)
    assert morpho_v2_prices.confirmNewPriceFeed(
        morpho_v2_vault,
        sender=governance.address,
    )

    morpho_v2_vault.setModes(0, 0, 0, convert_mode)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 0
    assert morpho_v2_prices.getLatestSnapshot(morpho_v2_vault).pricePerShare == 0


def test_morpho_v2_zero_supply_fails_closed_at_registration_and_runtime(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    morpho_v2_vault.setSupply(0)
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)

    morpho_v2_vault.setSupply(EIGHTEEN_DECIMALS)
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
    )
    morpho_v2_vault.setSupply(0)
    latest = morpho_v2_prices.getLatestSnapshot(morpho_v2_vault)
    assert latest.totalSupply == 0
    assert latest.pricePerShare == 0


def test_supply_times_price_per_share_exact_boundary_at_registration(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, 1)

    price_per_share = morpho_v2_vault.pricePerShare()
    max_normalized_supply = MAX_UINT256 // price_per_share
    morpho_v2_vault.setSupply(max_normalized_supply * EIGHTEEN_DECIMALS)
    assert _is_valid(morpho_v2_prices, morpho_v2_vault)

    morpho_v2_vault.setSupply((max_normalized_supply + 1) * EIGHTEEN_DECIMALS)
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)


def test_underlying_price_times_price_per_share_exact_boundary_at_registration(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    price_per_share = morpho_v2_vault.pricePerShare()
    max_underlying_price = MAX_UINT256 // price_per_share

    mock_price_source.setPrice(alpha_token, max_underlying_price)
    assert _is_valid(morpho_v2_prices, morpho_v2_vault)

    mock_price_source.setPrice(alpha_token, max_underlying_price + 1)
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)


@pytest.mark.parametrize(
    "modes",
    [
        (0, 0, 5, 0),
        (0, 0, 0, 5),
    ],
)
def test_mode_five_numeric_observations_are_rejected_when_incompatible(
    modes,
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
):
    morpho_v2_factory.setVault(morpho_v2_vault, True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    morpho_v2_vault.setModes(*modes)
    assert not _is_valid(morpho_v2_prices, morpho_v2_vault)


def test_numeric_dependencies_fail_closed_after_registration_and_recover(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
    )
    expected_price = 5 * EIGHTEEN_DECIMALS // 4
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == expected_price

    morpho_v2_vault.setModes(0, 0, 5, 0)
    latest = morpho_v2_prices.getLatestSnapshot(morpho_v2_vault)
    assert latest.totalSupply == 0
    assert latest.pricePerShare == 0

    morpho_v2_vault.setModes(0, 0, 0, 5)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 0
    assert morpho_v2_prices.getLatestSnapshot(morpho_v2_vault).pricePerShare == 0

    morpho_v2_vault.setModes(0, 0, 0, 0)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == expected_price
    latest = morpho_v2_prices.getLatestSnapshot(morpho_v2_vault)
    assert latest.totalSupply == 100
    assert latest.pricePerShare == morpho_v2_vault.pricePerShare()


def test_weighted_accumulation_overflow_fails_closed(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
    teller,
):
    individually_safe_price_per_share = MAX_UINT256 // 2 + 1
    morpho_v2_vault.setSupply(EIGHTEEN_DECIMALS)
    morpho_v2_vault.setConversionOverride(individually_safe_price_per_share, True)
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
        underlying_price=1,
        max_snapshots=2,
    )
    assert morpho_v2_prices.getWeightedPrice(morpho_v2_vault) == individually_safe_price_per_share

    boa.env.time_travel(seconds=1)
    assert morpho_v2_prices.addPriceSnapshot(morpho_v2_vault, sender=teller.address)
    assert morpho_v2_prices.getWeightedPrice(morpho_v2_vault) == 0


def test_underlying_price_multiplication_overflow_fails_closed_and_recovers(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    price_per_share = morpho_v2_vault.pricePerShare()
    max_underlying_price = MAX_UINT256 // price_per_share
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
        underlying_price=max_underlying_price,
    )
    expected = max_underlying_price * price_per_share // EIGHTEEN_DECIMALS
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == expected

    mock_price_source.setPrice(alpha_token, max_underlying_price + 1)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 0

    mock_price_source.setPrice(alpha_token, max_underlying_price)
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == expected


def test_upside_throttle_overflow_fails_closed(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    huge_price_per_share = MAX_UINT256 // 2
    morpho_v2_vault.setSupply(EIGHTEEN_DECIMALS)
    morpho_v2_vault.setConversionOverride(huge_price_per_share, True)
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
        underlying_price=1,
        max_upside=100_00,
    )

    assert morpho_v2_prices.getLatestSnapshot(morpho_v2_vault).pricePerShare == 0


def test_existing_erc4626_yield_vault_protocols_still_price(
    blue_chip_prices,
    governance,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_vault,
    bravo_token_vault,
    charlie_token_vault,
):
    cases = (
        (BLUE_CHIP_PROTOCOL_MORPHO, alpha_token, alpha_token_vault),
        (BLUE_CHIP_PROTOCOL_EULER, bravo_token, bravo_token_vault),
        (BLUE_CHIP_PROTOCOL_FLUID, charlie_token, charlie_token_vault),
    )
    for protocol, underlying, vault in cases:
        mock_price_source.setPrice(underlying, EIGHTEEN_DECIMALS)
        assert blue_chip_prices.isValidNewFeed(vault, protocol, 0, 5, 0, 100)
        blue_chip_prices.addNewPriceFeed(
            vault,
            protocol,
            0,
            5,
            0,
            100,
            sender=governance.address,
        )

    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    for _, _, vault in cases:
        assert blue_chip_prices.confirmNewPriceFeed(vault, sender=governance.address)
        latest = blue_chip_prices.getLatestSnapshot(vault)
        assert latest.totalSupply == 0
        assert latest.pricePerShare > 0
        assert blue_chip_prices.getPrice(vault) == EIGHTEEN_DECIMALS


def test_morpho_v2_update_confirmation_preserves_live_snapshot_progress(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
    teller,
):
    morpho_v2_vault.setSupply(100 * EIGHTEEN_DECIMALS)
    morpho_v2_vault.setPricePerShare(EIGHTEEN_DECIMALS)
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
        max_upside=1_000,
    )
    initial = morpho_v2_prices.priceConfigs(morpho_v2_vault)
    assert initial.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS
    assert initial.nextIndex == 1
    assert morpho_v2_prices.updatePriceConfig(
        morpho_v2_vault,
        0,
        5,
        1_000,
        100,
        sender=governance.address,
    )
    pending = morpho_v2_prices.pendingPriceConfigs(morpho_v2_vault).config
    assert pending.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS
    assert pending.nextIndex == 1

    morpho_v2_vault.setPricePerShare(EIGHTEEN_DECIMALS // 2)
    boa.env.time_travel(seconds=1)
    assert morpho_v2_prices.addPriceSnapshot(
        morpho_v2_vault,
        sender=teller.address,
    )
    morpho_v2_vault.setPricePerShare(8 * EIGHTEEN_DECIMALS // 10)
    boa.env.time_travel(seconds=1)
    assert morpho_v2_prices.addPriceSnapshot(
        morpho_v2_vault,
        sender=teller.address,
    )
    before = morpho_v2_prices.priceConfigs(morpho_v2_vault)
    assert before.lastSnapshot.pricePerShare == 55 * 10**16
    assert before.nextIndex == 3

    boa.env.time_travel(blocks=morpho_v2_prices.actionTimeLock() + 1)
    assert morpho_v2_prices.confirmPriceFeedUpdate(
        morpho_v2_vault,
        sender=governance.address,
    )
    after = morpho_v2_prices.priceConfigs(morpho_v2_vault)
    assert after.lastSnapshot.pricePerShare == 605 * 10**15
    assert after.nextIndex == 4
    written = morpho_v2_prices.snapShots(morpho_v2_vault, before.nextIndex)
    assert written.pricePerShare == after.lastSnapshot.pricePerShare
    assert written.lastUpdate == after.lastSnapshot.lastUpdate
    assert not morpho_v2_prices.hasPendingPriceFeedUpdate(morpho_v2_vault)


def test_morpho_v2_successful_zero_live_pps_control_remains_fail_closed(
    morpho_v2_prices,
    morpho_v2_factory,
    morpho_v2_vault,
    alpha_token,
    mock_price_source,
    governance,
):
    morpho_v2_vault.setSupply(100 * EIGHTEEN_DECIMALS)
    morpho_v2_vault.setPricePerShare(EIGHTEEN_DECIMALS)
    _register(
        morpho_v2_prices,
        morpho_v2_factory,
        morpho_v2_vault,
        alpha_token,
        mock_price_source,
        governance,
    )
    assert morpho_v2_prices.getWeightedPrice(morpho_v2_vault) > 0
    morpho_v2_vault.setPricePerShare(0)
    assert morpho_v2_vault.pricePerShare() == 0
    assert morpho_v2_prices.getPrice(morpho_v2_vault) == 0
