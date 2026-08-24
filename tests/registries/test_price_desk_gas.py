from pathlib import Path

import boa
import pytest

from config.robinhood_launch import STALE_WINDOW_GLOBAL
from conf_utils import advance_timelock_blocks
from constants import (
    BLUE_CHIP_PROTOCOL_MORPHO,
    BLUE_CHIP_PROTOCOL_MORPHO_V2,
    EIGHTEEN_DECIMALS,
    ZERO_ADDRESS,
)
ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
EIP_170_LIMIT = 24_576
PRODUCTION_PRICE_SOURCES = {
    "AeroRipePrices.vy",
    "BlueChipYieldPrices.vy",
    "ChainlinkPrices.vy",
    "CurvePrices.vy",
    "PythPrices.vy",
    "RedStone.vy",
    "StorkPrices.vy",
    "UndyVaultPrices.vy",
    "UniswapV2Prices.vy",
    "wsuperOETHbPrices.vy",
}
QUALIFIED_GLOBAL_STALE_TIME = 86_400

if STALE_WINDOW_GLOBAL != QUALIFIED_GLOBAL_STALE_TIME:
    raise RuntimeError(
        "Robinhood global stale-time policy changed; rerun PriceDesk gas "
        "qualification before updating QUALIFIED_GLOBAL_STALE_TIME"
    )


@pytest.fixture(autouse=True)
def valid_global_stale_time(mission_control):
    """Run gas qualifications with the production one-day global policy."""

    with boa.env.anchor():
        mission_control.eval(
            f"self.genConfig.priceStaleTime = {STALE_WINDOW_GLOBAL}"
        )
        yield


FOUR_COIN_CURVE_SYSTEM = """# @version 0.4.3
coins: address[4]

@deploy
def __init__(_coins: address[4]):
    self.coins = _coins

@view
@external
def get_address(_id: uint256) -> address:
    if _id == 7 or _id == 12:
        return self
    return empty(address)

@view
@external
def is_registered(_pool: address) -> bool:
    return True

@view
@external
def get_lp_token(_pool: address) -> address:
    return self

@view
@external
def get_underlying_coins(_pool: address) -> address[8]:
    return [
        self.coins[0], self.coins[1], self.coins[2], self.coins[3],
        empty(address), empty(address), empty(address), empty(address),
    ]

@view
@external
def get_n_underlying_coins(_pool: address) -> uint256:
    return 4

@view
@external
def get_registry_handlers_from_pool(_pool: address) -> address[10]:
    return [
        self, empty(address), empty(address), empty(address), empty(address),
        empty(address), empty(address), empty(address), empty(address), empty(address),
    ]

@view
@external
def get_base_registry(_handler: address) -> address:
    return self

@view
@external
def totalSupply() -> uint256:
    return 1

@view
@external
def get_virtual_price() -> uint256:
    return 10**18
"""


def _set_priorities(mission_control, switchboard_alpha, source_ids):
    mission_control.setPriorityPriceSourceIds(
        source_ids,
        sender=switchboard_alpha.address,
    )


def _register_source(desk, source, deployer, description):
    assert desk.startAddNewAddressToRegistry(source, description, sender=deployer)
    return desk.confirmNewAddressToRegistry(source, sender=deployer)


def _isolated_price_desk(ripe_hq, deploy3r, sources, price_limit=None):
    source_path = Path("contracts/registries/PriceDesk.vy")
    if price_limit is None:
        desk = boa.load(
            str(source_path),
            ripe_hq,
            deploy3r,
            ETH,
            1,
            2,
            name="gas_measurement_price_desk",
        )
    else:
        source = source_path.read_text().replace(
            "PRICE_SOURCE_PRICE_GAS: constant(uint256) = 250_000",
            f"PRICE_SOURCE_PRICE_GAS: constant(uint256) = {price_limit}",
            1,
        )
        desk = boa.loads(
            source,
            ripe_hq,
            deploy3r,
            ETH,
            1,
            2,
            name=f"gas_boundary_price_desk_{price_limit}",
            filename=str(source_path),
        )
    for index, source in enumerate(sources, start=1):
        assert _register_source(desk, source, deploy3r, f"gas source {index}") == index
    return desk


def _measure_price(desk, asset, expected):
    assert desk.getPrice(asset, True) == expected
    return desk._computation.get_gas_used()


def _measure_has_feed(desk, asset):
    assert desk.hasPriceFeed(asset)
    return desk._computation.get_gas_used()


def _configure_max_bluechip_feed(
    blue_chip_prices,
    governance,
    teller,
    mock_price_source,
    token,
    vault,
    whale,
):
    unit = 10 ** token.decimals()
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    token.approve(vault, 100 * unit, sender=whale)
    vault.deposit(100 * unit, whale, sender=whale)
    assert blue_chip_prices.addNewPriceFeed(
        vault,
        BLUE_CHIP_PROTOCOL_MORPHO,
        0,
        25,
        0,
        0,
        sender=governance.address,
    )
    advance_timelock_blocks(blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(vault, sender=governance.address)
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert blue_chip_prices.addPriceSnapshot(vault, sender=teller.address)


@pytest.mark.gas
def test_price_desk_complete_deployed_runtime_is_below_eip170(price_desk):
    deployed_runtime = bytes(boa.env.get_code(price_desk.address))
    assert len(deployed_runtime) < EIP_170_LIMIT
    print(
        "PRICEDESK_DEPLOYED_RUNTIME",
        f"size={len(deployed_runtime)}",
        f"headroom={EIP_170_LIMIT - len(deployed_runtime)}",
    )


@pytest.mark.gas
def test_price_source_inventory_and_flat_operation_gas(
    price_desk,
    chainlink,
    pyth_prices,
    stork_prices,
    governance,
    mission_control,
    switchboard_alpha,
    sally,
    alpha_token,
    bravo_token,
):
    source_dir = Path("contracts/priceSources")
    assert {path.name for path in source_dir.glob("*.vy")} == PRODUCTION_PRICE_SOURCES

    _set_priorities(mission_control, switchboard_alpha, [1])
    chainlink_price = _measure_price(price_desk, sally, EIGHTEEN_DECIMALS)
    chainlink_feed = _measure_has_feed(price_desk, sally)

    pyth_id = bytes.fromhex(
        "eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a"
    )
    assert pyth_prices.addNewPriceFeed(
        alpha_token, pyth_id, 0, sender=governance.address
    )
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    _set_priorities(mission_control, switchboard_alpha, [4])
    expected_pyth = pyth_prices.getPrice(alpha_token)
    pyth_price = _measure_price(price_desk, alpha_token, expected_pyth)
    pyth_feed = _measure_has_feed(price_desk, alpha_token)

    stork_id = bytes.fromhex(
        "7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c"
    )
    assert stork_prices.addNewPriceFeed(
        bravo_token, stork_id, 0, sender=governance.address
    )
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmNewPriceFeed(bravo_token, sender=governance.address)
    _set_priorities(mission_control, switchboard_alpha, [5])
    expected_stork = stork_prices.getPrice(bravo_token)
    stork_price = _measure_price(price_desk, bravo_token, expected_stork)
    stork_feed = _measure_has_feed(price_desk, bravo_token)

    print(
        "PRICEDESK_FLAT_GAS",
        f"chainlink_price={chainlink_price}",
        f"chainlink_has_feed={chainlink_feed}",
        f"pyth_price={pyth_price}",
        f"pyth_has_feed={pyth_feed}",
        f"stork_price={stork_price}",
        f"stork_has_feed={stork_feed}",
    )
    assert max(chainlink_price, pyth_price, stork_price) < 250_000
    assert max(chainlink_feed, pyth_feed, stork_feed) < 75_000


@pytest.mark.gas
def test_redstone_flat_and_nested_cross_asset_price_gas(
    price_desk,
    chainlink,
    redstone,
    governance,
    mission_control,
    switchboard_alpha,
    mock_chainlink_feed_one,
    mock_chainlink_feed_two,
    alpha_token,
    bravo_token,
):
    eth = redstone.ETH()
    assert chainlink.addNewPriceFeed(
        eth,
        mock_chainlink_feed_one,
        0,
        False,
        False,
        sender=governance.address,
    )
    advance_timelock_blocks(chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(eth, sender=governance.address)

    assert redstone.addNewPriceFeed(
        alpha_token,
        mock_chainlink_feed_two,
        0,
        False,
        sender=governance.address,
    )
    assert redstone.addNewPriceFeed(
        bravo_token,
        mock_chainlink_feed_two,
        0,
        True,
        sender=governance.address,
    )
    advance_timelock_blocks(redstone.actionTimeLock() + 1)
    assert redstone.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert redstone.confirmNewPriceFeed(bravo_token, sender=governance.address)

    _set_priorities(mission_control, switchboard_alpha, [9, 1])
    flat_gas = _measure_price(price_desk, alpha_token, EIGHTEEN_DECIMALS)
    nested_gas = _measure_price(price_desk, bravo_token, EIGHTEEN_DECIMALS)
    feed_gas = _measure_has_feed(price_desk, bravo_token)
    print(
        "PRICEDESK_REDSTONE_GAS",
        f"flat={flat_gas}",
        f"nested_eth_usd={nested_gas}",
        f"has_feed={feed_gas}",
    )
    assert nested_gas < 250_000
    assert feed_gas < 75_000


@pytest.mark.gas
def test_bluechip_and_undy_max_snapshot_nested_price_and_snapshot_gas(
    price_desk,
    blue_chip_prices,
    undy_vault_prices,
    governance,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    alpha_token_vault,
    alpha_token_whale,
    bravo_token,
    bravo_token_vault,
    bravo_token_whale,
    teller,
):
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    alpha_token.approve(
        alpha_token_vault,
        100 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    alpha_token_vault.deposit(
        100 * EIGHTEEN_DECIMALS,
        alpha_token_whale,
        sender=alpha_token_whale,
    )
    assert blue_chip_prices.addNewPriceFeed(
        alpha_token_vault,
        BLUE_CHIP_PROTOCOL_MORPHO,
        0,
        25,
        0,
        0,
        sender=governance.address,
    )
    advance_timelock_blocks(blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(
        alpha_token_vault,
        sender=governance.address,
    )
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert blue_chip_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
    _set_priorities(mission_control, switchboard_alpha, [3, 6])
    bluechip_price = _measure_price(
        price_desk,
        alpha_token_vault,
        EIGHTEEN_DECIMALS,
    )
    bluechip_feed = _measure_has_feed(price_desk, alpha_token_vault)
    boa.env.time_travel(seconds=1)
    assert price_desk.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    bluechip_snapshot = price_desk._computation.get_gas_used()

    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    bravo_token.approve(
        bravo_token_vault,
        100 * EIGHTEEN_DECIMALS,
        sender=bravo_token_whale,
    )
    bravo_token_vault.deposit(
        100 * EIGHTEEN_DECIMALS,
        bravo_token_whale,
        sender=bravo_token_whale,
    )
    assert undy_vault_prices.addNewPriceFeed(
        bravo_token_vault,
        0,
        25,
        0,
        0,
        sender=governance.address,
    )
    advance_timelock_blocks(undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmNewPriceFeed(
        bravo_token_vault,
        sender=governance.address,
    )
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert undy_vault_prices.addPriceSnapshot(
            bravo_token_vault,
            sender=teller.address,
        )
    _set_priorities(mission_control, switchboard_alpha, [10, 6])
    undy_price = _measure_price(
        price_desk,
        bravo_token_vault,
        2 * EIGHTEEN_DECIMALS,
    )
    undy_feed = _measure_has_feed(price_desk, bravo_token_vault)
    boa.env.time_travel(seconds=1)
    assert price_desk.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    undy_snapshot = price_desk._computation.get_gas_used()

    print(
        "PRICEDESK_YIELD_GAS",
        f"bluechip_price_25_nested={bluechip_price}",
        f"bluechip_has_feed={bluechip_feed}",
        f"bluechip_registry_snapshot={bluechip_snapshot}",
        f"undy_price_25_nested={undy_price}",
        f"undy_has_feed={undy_feed}",
        f"undy_registry_snapshot={undy_snapshot}",
    )
    assert max(bluechip_price, undy_price) < 250_000
    assert max(bluechip_feed, undy_feed) < 75_000
    assert max(bluechip_snapshot, undy_snapshot) < 150_000


@pytest.mark.gas
def test_selected_morpho_v2_full_ring_nested_pricedesk_gas(
    ripe_hq,
    deploy3r,
    governance,
    teller,
    chainlink,
    curve_prices,
    mission_control,
    switchboard_alpha,
    alpha_token,
    mock_chainlink_feed_one,
):
    assert chainlink.addNewPriceFeed(
        alpha_token,
        mock_chainlink_feed_one,
        0,
        False,
        False,
        sender=governance.address,
    )
    advance_timelock_blocks(chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    factory = boa.load(
        "contracts/mock/MockMorphoV2Factory.vy",
        name="pricedesk_gas_morpho_v2_factory",
    )
    vault = boa.load(
        "contracts/mock/MockMorphoV2Vault.vy",
        alpha_token,
        18,
        100 * EIGHTEEN_DECIMALS,
        125 * EIGHTEEN_DECIMALS // 100,
        name="pricedesk_gas_morpho_v2_vault",
    )
    factory.setVault(vault, True)
    blue_chip = boa.load(
        "contracts/priceSources/BlueChipYieldPrices.vy",
        ripe_hq,
        deploy3r,
        1,
        2,
        [ZERO_ADDRESS, ZERO_ADDRESS],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        factory,
        name="pricedesk_gas_selected_morpho_v2",
    )
    assert blue_chip.addNewPriceFeed(
        vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        25,
        0,
        100,
        sender=deploy3r,
    )
    assert blue_chip.confirmNewPriceFeed(vault, sender=deploy3r)
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert blue_chip.addPriceSnapshot(vault, sender=teller.address)
    config = blue_chip.priceConfigs(vault)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO_V2
    assert config.underlyingAsset == alpha_token.address
    assert config.maxNumSnapshots == 25
    assert config.nextIndex == 0

    desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [chainlink, curve_prices, blue_chip],
    )
    # Candidate snapshot authorization accepts any registered Ripe department.
    # Register this isolated three-slot desk solely for the test transaction.
    assert ripe_hq.startAddNewAddressToRegistry(
        desk,
        "Morpho V2 gas desk",
        sender=governance.address,
    )
    advance_timelock_blocks(ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmNewAddressToRegistry(desk, sender=governance.address)
    # The registry timelock advances past the configured feed/snapshot stale
    # windows; refresh both without changing the already-filled ring capacity.
    mock_chainlink_feed_one.setMockData(10**8)
    assert blue_chip.addPriceSnapshot(vault, sender=teller.address)
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    assert desk.numAddrs() - 1 == 3
    assert tuple(mission_control.getPriorityPriceSourceIds()) == (1, 2)

    expected = 125 * EIGHTEEN_DECIMALS // 100
    price_gas = _measure_price(desk, vault, expected)
    feed_gas = _measure_has_feed(desk, vault)
    boa.env.time_travel(seconds=1)
    assert desk.addPriceSnapshot(vault, sender=teller.address)
    snapshot_gas = desk._computation.get_gas_used()
    print(
        "PRICEDESK_MORPHO_V2_GAS",
        f"price_25_nested={price_gas}",
        f"has_feed={feed_gas}",
        f"registry_snapshot={snapshot_gas}",
        "source_slots=3",
        "priority_source_ids=(1,2)",
        "snapshot_capacity=25",
    )
    assert price_gas < 250_000
    assert feed_gas < 75_000
    assert snapshot_gas < 150_000


@pytest.mark.gas
def test_four_coin_curve_nested_price_succeeds_in_final_registry_position(
    ripe_hq,
    deploy3r,
    governance,
    green_token,
    savings_green,
    mission_control,
    switchboard_alpha,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
):
    coins = [alpha_token, bravo_token, charlie_token, delta_token]
    for coin in coins:
        mock_price_source.setPrice(coin, EIGHTEEN_DECIMALS)
    _set_priorities(mission_control, switchboard_alpha, [6])

    curve_system = boa.loads(
        FOUR_COIN_CURVE_SYSTEM,
        [coin.address for coin in coins],
        name="four_coin_curve_gas_system",
    )
    curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        curve_system,
        green_token,
        savings_green,
        1,
        2,
        name="four_coin_curve_gas_source",
    )
    assert curve.addNewPriceFeed(
        curve_system,
        curve_system,
        sender=governance.address,
    )
    assert curve.confirmNewPriceFeed(curve_system, sender=governance.address)

    no_feed_sources = []
    for index in range(8):
        source = boa.load(
            "contracts/mock/MockRawPriceSource.vy",
            name=f"curve_no_feed_{index}",
        )
        source.configure(0, False)
        no_feed_sources.append(source)
    desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [*no_feed_sources, mock_price_source, curve],
    )
    _set_priorities(mission_control, switchboard_alpha, [1, 2, 3])

    assert desk.numAddrs() - 1 == 10
    curve_gas = _measure_price(desk, curve_system, EIGHTEEN_DECIMALS)
    curve_feed_gas = _measure_has_feed(desk, curve_system)
    config = curve.curveConfig(curve_system)
    assert config.numUnderlying == 4
    assert tuple(config.underlying) == tuple(coin.address for coin in coins)
    for coin in coins:
        assert not curve.hasPriceFeed(coin)

    hostile_sources = []
    for index in range(9):
        source = boa.load(
            "contracts/mock/MockGasBurningPriceSource.vy",
            name=f"curve_hostile_source_{index}",
        )
        source.configure(
            EIGHTEEN_DECIMALS,
            True,
            1_000_000,
            0,
            0,
            True,
            False,
            False,
        )
        source.setPriceBurnAsset(curve_system)
        hostile_sources.append(source)
    hostile_desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [*hostile_sources, curve],
    )
    _set_priorities(mission_control, switchboard_alpha, [6, 1, 2, 3])
    assert hostile_desk.numAddrs() - 1 == 10
    assert hostile_desk.getPrice(curve_system, True, gas=6_000_000) == EIGHTEEN_DECIMALS
    hostile_curve_gas = hostile_desk._computation.get_gas_used()

    one_hostile_desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [hostile_sources[0], no_feed_sources[0], curve],
    )
    _set_priorities(mission_control, switchboard_alpha, [1])
    assert (
        one_hostile_desk.getPrice(curve_system, True, gas=3_000_000)
        == EIGHTEEN_DECIMALS
    )
    one_hostile_curve_gas = one_hostile_desk._computation.get_gas_used()

    _set_priorities(mission_control, switchboard_alpha, [1, 2, 3])
    boundary_results = {}
    for price_limit in range(80_000, 150_001, 10_000):
        boundary_desk = _isolated_price_desk(
            ripe_hq,
            deploy3r,
            [*no_feed_sources, mock_price_source, curve],
            price_limit=price_limit,
        )
        boundary_results[price_limit] = (
            boundary_desk.getPrice(
                curve_system,
                False,
                gas=6_000_000,
            )
            == EIGHTEEN_DECIMALS
        )
    minimum_success = min(
        limit for limit, succeeded in boundary_results.items() if succeeded
    )
    assert not boundary_results[90_000]
    assert minimum_success == 110_000
    print(
        "PRICEDESK_CURVE_GAS",
        f"four_coin_nested_final_position={curve_gas}",
        f"four_coin_nested_behind_one_hostile={one_hostile_curve_gas}",
        f"four_coin_nested_behind_nine_hostile={hostile_curve_gas}",
        f"four_coin_has_feed_final_position={curve_feed_gas}",
        f"forwarded_boundary_10k_resolution={minimum_success}",
        f"boundary_results={boundary_results}",
        "source_slots=10",
        "outer_limit=6000000",
    )
    assert curve_gas < 2_000_000
    assert one_hostile_curve_gas < 3_000_000
    assert hostile_curve_gas < 6_000_000
    assert curve_feed_gas < 75_000


@pytest.mark.gas
def test_four_coin_curve_over_max_snapshot_bluechip_is_rejected_at_confirmation(
    ripe_hq,
    deploy3r,
    governance,
    teller,
    green_token,
    savings_green,
    mission_control,
    switchboard_alpha,
    price_desk,
    mock_price_source,
    blue_chip_prices,
    alpha_token,
    alpha_token_vault,
    alpha_token_whale,
    bravo_token,
    bravo_token_vault,
    bravo_token_whale,
    charlie_token,
    charlie_token_vault,
    charlie_token_whale,
    delta_token,
    delta_token_vault,
    delta_token_whale,
):
    feeds = (
        (alpha_token, alpha_token_vault, alpha_token_whale),
        (bravo_token, bravo_token_vault, bravo_token_whale),
        (charlie_token, charlie_token_vault, charlie_token_whale),
        (delta_token, delta_token_vault, delta_token_whale),
    )
    for token, vault, whale in feeds:
        _configure_max_bluechip_feed(
            blue_chip_prices,
            governance,
            teller,
            mock_price_source,
            token,
            vault,
            whale,
        )
    vaults = [vault.address for _, vault, _ in feeds]
    curve_system = boa.loads(
        FOUR_COIN_CURVE_SYSTEM,
        vaults,
        name="four_bluechip_coin_curve_gas_system",
    )
    old_pool = boa.loads(
        FOUR_COIN_CURVE_SYSTEM,
        vaults,
        name="four_bluechip_coin_old_pool",
    )
    new_pool = boa.loads(
        FOUR_COIN_CURVE_SYSTEM,
        vaults,
        name="four_bluechip_coin_new_pool",
    )
    curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        curve_system,
        green_token,
        savings_green,
        1,
        2,
        name="four_bluechip_coin_curve_gas_source",
    )

    # First activate a cheap exact route so the update path can prove atomic
    # rollback against a real previous configuration.
    _set_priorities(mission_control, switchboard_alpha, [6])
    assert curve.addNewPriceFeed(
        curve_system,
        old_pool,
        sender=governance.address,
    )
    assert curve.confirmNewPriceFeed(curve_system, sender=governance.address)
    previous = curve.curveConfig(curve_system)

    # Exercise the expensive but governance-reachable canonical topology: each
    # Curve underlying traverses the other registered sources before reaching
    # BlueChipYieldPrices, while the final mock source remains a healthy
    # aggregate fallback for the LP token itself.
    _set_priorities(
        mission_control,
        switchboard_alpha,
        [1, 2, 4, 5, 7, 8, 9, 10, 3, 6],
    )
    assert curve.updatePriceFeed(
        curve_system,
        new_pool,
        sender=governance.address,
    )
    update_action = curve.pendingUpdates(curve_system).actionId

    mock_price_source.setPrice(curve_system, EIGHTEEN_DECIMALS)
    assert price_desk.getPrice(curve_system) == EIGHTEEN_DECIMALS
    with boa.reverts("price source not executable"):
        curve.confirmPriceFeedUpdate(curve_system, sender=governance.address)

    assert curve.pendingUpdates(curve_system).actionId == update_action
    assert curve.curveConfig(curve_system) == previous

    # A fresh source proves the same exact-stipend rejection for new feeds.
    new_curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        curve_system,
        green_token,
        savings_green,
        1,
        2,
        name="four_bluechip_coin_new_curve_gas_source",
    )
    assert new_curve.addNewPriceFeed(
        curve_system,
        new_pool,
        sender=governance.address,
    )
    pending_action = new_curve.pendingUpdates(curve_system).actionId

    # A healthy fallback would make an aggregate PriceDesk query pass, but must
    # not mask that this exact Curve source exceeds the live 250k stipend.
    mock_price_source.setPrice(curve_system, EIGHTEEN_DECIMALS)
    assert price_desk.getPrice(curve_system) == EIGHTEEN_DECIMALS
    with boa.reverts("price source not executable"):
        new_curve.confirmNewPriceFeed(curve_system, sender=governance.address)

    assert new_curve.pendingUpdates(curve_system).actionId == pending_action
    assert new_curve.curveConfig(curve_system).pool == ZERO_ADDRESS
    assert not new_curve.hasPriceFeed(curve_system)


@pytest.mark.gas
def test_wsuper_oethb_nested_price_gas(
    ripe_hq,
    deploy3r,
    alpha_token,
    alpha_token_vault,
    mock_price_source,
    mission_control,
    switchboard_alpha,
):
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    wrapped = boa.load(
        "contracts/priceSources/wsuperOETHbPrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        alpha_token,
        alpha_token_vault,
        ZERO_ADDRESS,
        1,
        2,
        name="wsuper_oethb_nested_gas_source",
    )
    desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [mock_price_source, wrapped],
    )
    _set_priorities(mission_control, switchboard_alpha, [2, 1])
    nested_gas = _measure_price(
        desk,
        alpha_token_vault,
        EIGHTEEN_DECIMALS,
    )
    feed_gas = _measure_has_feed(desk, alpha_token_vault)
    print(
        "PRICEDESK_WSUPER_GAS",
        f"nested_price={nested_gas}",
        f"has_feed={feed_gas}",
    )
    assert nested_gas < 250_000
    assert feed_gas < 75_000
