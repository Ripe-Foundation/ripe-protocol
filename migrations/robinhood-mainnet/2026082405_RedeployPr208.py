"""Deploy the Robinhood contracts changed by the merged PR-208 generation.

RipeHq, tokens, CCIP pools, Ledger, MissionControl, and every unchanged
department remain active.  This migration deploys eleven candidates, builds
the two fresh child-registry trees, copies live oracle routes, relinquishes all
temporary local governance, and prints one readable Safe batch.  It does not
change live registry wiring itself.

Teller follows the reviewed launch policy and is constructed paused.  The Safe
batch confirms the fresh SwitchboardCharlie before using it to unpause Teller.
All registry and action delays involved in this replacement are already zero.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PYTH_PRICES_ID,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    STALE_WINDOW_INHERIT,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
    stale_time_override_for_asset,
)


CANDIDATE_SUFFIX = "Candidate2026082405"
LIVE_CURVE_ADDRESS_PROVIDER = "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648"

HQ_REPLACEMENTS = (
    ("PriceDesk", 7),
    ("VaultBook", 8),
    ("CreditEngine", 13),
    ("Endaoment", 14),
    ("Teller", 17),
)
SWITCHBOARD_REPLACEMENTS = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
)


def candidate_label(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def _as_address(value):
    return str(getattr(value, "address", value)).lower()


def _assert_slot(registry, migration, name, reg_id):
    expected = migration.get_address(name)
    actual = registry.getAddr(reg_id)
    if _as_address(actual) != _as_address(expected):
        raise RuntimeError(f"PR208_ACTIVE_SLOT_MISMATCH:{name}:{reg_id}")


def _assert_live_graph(migration, hq, switchboard, price_desk, vault_book):
    for name, reg_id in HQ_REPLACEMENTS:
        _assert_slot(hq, migration, name, reg_id)
    for name, reg_id in SWITCHBOARD_REPLACEMENTS:
        _assert_slot(switchboard, migration, name, reg_id)
    for name, reg_id in (
        ("ChainlinkPrices", 1),
        ("CurvePrices", 2),
        ("UniswapV2Prices", 3),
    ):
        _assert_slot(price_desk, migration, name, reg_id)
    for name, reg_id in (
        ("StabilityPool", 1),
        ("RipeGov", 2),
        ("SimpleErc20", 3),
    ):
        _assert_slot(vault_book, migration, name, reg_id)


def _register(migration, registry, contract, name, expected_id):
    def started_or_done():
        if int(registry.getRegId(contract)) == expected_id:
            return True
        pending = registry.pendingNewAddr(contract)
        return str(pending[0]) == name and int(pending[2]) != 0

    assert migration.execute_reconciled(
        registry.startAddNewAddressToRegistry,
        started_or_done,
        contract,
        name,
    )
    assert migration.execute_reconciled(
        registry.confirmNewAddressToRegistry,
        lambda: int(registry.getRegId(contract)) == expected_id,
        contract,
    )
    assert int(registry.getRegId(contract)) == expected_id


def _relinquish_gov(migration, contract):
    assert _as_address(contract.governance()) in (
        _as_address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: _as_address(contract.governance()) == ZERO_ADDRESS,
    )
    assert _as_address(contract.governance()) == ZERO_ADDRESS


def _chainlink_config(config):
    return (
        _as_address(config[0]),
        int(config[1]),
        bool(config[2]),
        bool(config[3]),
        int(config[4]),
    )


def _chainlink_route_matches(chainlink, asset, expected):
    return _chainlink_config(chainlink.feedConfig(asset)) == expected


def _chainlink_route_started(chainlink, asset, expected):
    if _chainlink_route_matches(chainlink, asset, expected):
        return True
    pending = chainlink.pendingUpdates(asset)
    return int(pending[0]) != 0 and _chainlink_config(pending[1]) == expected


def _asset_label(asset):
    """Best-effort token symbol for the operator-facing Safe plan."""
    import boa

    abi = (
        '[{"type":"function","name":"symbol","stateMutability":"view",'
        '"inputs":[],"outputs":[{"name":"","type":"string"}]}]'
    )
    try:
        symbol = str(boa.loads_abi(abi).at(asset).symbol()).strip()
    except Exception:
        symbol = ""
    if symbol and all(character.isprintable() for character in symbol):
        return symbol[:24]
    value = str(asset)
    return f"{value[:8]}…{value[-6:]}"


def _is_nft(config):
    return bool(config.isNft) if hasattr(config, "isNft") else bool(config[-1])


def _sync_token_scales(migration, price_desk, mission_control, eth, usdg):
    eth = _as_address(eth)
    synced = set()
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        normalized = _as_address(asset)
        if normalized in (ZERO_ADDRESS, eth) or _is_nft(
            mission_control.assetConfig(asset)
        ):
            continue
        assert migration.execute_reconciled(
            price_desk.syncTokenScale,
            lambda asset=asset: int(price_desk.tokenScale(asset)) != 0,
            asset,
        )
        synced.add(normalized)
    if _as_address(usdg) not in synced:
        assert migration.execute_reconciled(
            price_desk.syncTokenScale,
            lambda: int(price_desk.tokenScale(usdg)) != 0,
            usdg,
        )


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    switchboard = migration.get_contract("Switchboard")
    active_price_desk = migration.get_contract("PriceDesk")
    active_vault_book = migration.get_contract("VaultBook")
    _assert_live_graph(
        migration,
        hq,
        switchboard,
        active_price_desk,
        active_vault_book,
    )

    deployer = migration.account()
    active_chainlink = migration.get_contract("ChainlinkPrices")
    active_curve = migration.get_contract("CurvePrices")
    mission_control = migration.get_contract("MissionControl")
    endaoment_psm = migration.get_contract("EndaomentPSM")
    eth = active_price_desk.ETH()
    weth = active_chainlink.WETH()
    btc = active_chainlink.BTC()
    eth_feed = active_chainlink.feedConfig(eth)[0]
    btc_feed = active_chainlink.feedConfig(btc)[0]
    usdg = endaoment_psm.USDC()

    core_chainlink_assets = {_as_address(eth), _as_address(weth), _as_address(btc)}
    chainlink_routes = []
    for asset in active_chainlink.getPricedAssets():
        active = active_chainlink.feedConfig(asset)
        target = (
            _as_address(active[0]),
            int(active[1]),
            bool(active[2]),
            bool(active[3]),
            stale_time_override_for_asset(str(asset)),
        )
        if _as_address(asset) in core_chainlink_assets:
            assert target[4] == STALE_WINDOW_INHERIT
            continue
        chainlink_routes.append((_asset_label(asset), asset, target))

    curve_routes = []
    for asset in active_curve.getPricedAssets():
        config = active_curve.curveConfig(asset)
        curve_routes.append((_asset_label(asset), asset, config[0]))
    green = migration.get_address("GreenToken")
    curve_routes.sort(key=lambda route: _as_address(route[1]) != _as_address(green))
    green_ref = active_curve.greenRefPoolConfig()
    green_ref_values = tuple(int(green_ref[index]) for index in range(5, 10))

    log.h1("Deploying the merged RH oracle generation")
    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        deployer,
        eth,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate_label("PriceDesk"),
    )
    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        deployer,
        PRICE_MIN_TIMELOCK,
        PRICE_MAX_TIMELOCK,
        weth,
        eth,
        btc,
        eth_feed,
        btc_feed,
        STALE_WINDOW_INHERIT,
        label=candidate_label("ChainlinkPrices"),
    )
    for asset in (eth, weth, btc):
        active = active_chainlink.feedConfig(asset)
        expected = (
            _as_address(active[0]),
            int(active[1]),
            bool(active[2]),
            bool(active[3]),
            STALE_WINDOW_INHERIT,
        )
        assert _chainlink_route_matches(chainlink, asset, expected)
    for symbol, asset, expected in chainlink_routes:
        log.info(f"Adding Chainlink route {symbol:<6} with stale override {expected[4]}")
        assert migration.execute_reconciled(
            chainlink.addNewPriceFeed,
            lambda asset=asset, expected=expected: _chainlink_route_started(
                chainlink, asset, expected
            ),
            asset,
            expected[0],
            expected[4],
            expected[2],
            expected[3],
        )
        assert migration.execute_reconciled(
            chainlink.confirmNewPriceFeed,
            lambda asset=asset, expected=expected: _chainlink_route_matches(
                chainlink, asset, expected
            ),
            asset,
        )
    _register(migration, price_desk, chainlink, "ChainlinkPrices", 1)

    curve = migration.deploy(
        "CurvePrices",
        hq,
        deployer,
        LIVE_CURVE_ADDRESS_PROVIDER,
        green,
        migration.get_address("SavingsGreen"),
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
        label=candidate_label("CurvePrices"),
    )
    _register(migration, price_desk, curve, "CurvePrices", 2)
    _register(
        migration,
        price_desk,
        migration.get_contract("UniswapV2Prices"),
        "UniswapV2Prices",
        3,
    )
    _sync_token_scales(migration, price_desk, mission_control, eth, usdg)
    for contract in (chainlink, curve, price_desk):
        _relinquish_gov(migration, contract)

    log.h1("Deploying the merged RH vault generation")
    vault_book = migration.deploy(
        "VaultBook",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate_label("VaultBook"),
    )
    stability_pool = migration.deploy(
        "StabilityPool", hq, label=candidate_label("StabilityPool")
    )
    _register(migration, vault_book, stability_pool, "StabilityPool", 1)
    _register(migration, vault_book, migration.get_contract("RipeGov"), "RipeGov", 2)
    _register(
        migration,
        vault_book,
        migration.get_contract("SimpleErc20"),
        "SimpleErc20",
        3,
    )
    _relinquish_gov(migration, vault_book)

    log.h1("Deploying the merged RH switchboards")
    alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        deployer,
        STALE_WINDOW_MIN,
        STALE_WINDOW_MAX,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        PYTH_PRICES_ID,
        label=candidate_label("SwitchboardAlpha"),
    )
    bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        deployer,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=candidate_label("SwitchboardBravo"),
    )
    charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        deployer,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=candidate_label("SwitchboardCharlie"),
    )
    for contract in (alpha, bravo, charlie):
        _relinquish_gov(migration, contract)

    log.h1("Deploying the merged RH departments")
    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
        CURVE_PRICES_ID,
        label=candidate_label("CreditEngine"),
    )
    endaoment = migration.deploy(
        "Endaoment",
        hq,
        weth,
        eth,
        CURVE_PRICES_ID,
        label=candidate_label("Endaoment"),
    )
    teller = migration.deploy(
        "Teller",
        hq,
        TELLER_SHOULD_PAUSE,
        CURVE_PRICES_ID,
        label=candidate_label("Teller"),
    )
    assert bool(teller.isPaused()) is TELLER_SHOULD_PAUSE

    hq_updates = (
        ("PriceDesk", 7, price_desk.address),
        ("VaultBook", 8, vault_book.address),
        ("CreditEngine", 13, credit_engine.address),
        ("Endaoment", 14, endaoment.address),
        ("Teller", 17, teller.address),
    )
    switchboard_updates = (
        ("SwitchboardAlpha", 1, alpha.address),
        ("SwitchboardBravo", 2, bravo.address),
        ("SwitchboardCharlie", 3, charlie.address),
    )

    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0
    log.h1("One atomic Safe batch")
    log.info("// Start the five RipeHq replacements")
    for name, reg_id, address in hq_updates:
        log.info(
            f'await c.Ripe_RH_RipeHq.startAddressUpdateToRegistry('
            f'{reg_id}n, "{address}")  // {name}'
        )
    log.info("// Start the three Switchboard replacements")
    for name, reg_id, address in switchboard_updates:
        log.info(
            f'await c.Ripe_RH_Switchboard.startAddressUpdateToRegistry('
            f'{reg_id}n, "{address}")  // {name}'
        )

    log.info("// Make the fresh PriceDesk canonical before configuring Curve")
    log.info(
        "await c.Ripe_RH_RipeHq.confirmAddressUpdateToRegistry(7n)  // PriceDesk"
    )
    log.info(f'const cprices = c.Ripe_RH_CurvePrices.at("{curve.address}")')
    for symbol, asset, pool in curve_routes:
        log.info(f'await cprices.addNewPriceFeed("{asset}", "{pool}")  // {symbol}')
        log.info(f'await cprices.confirmNewPriceFeed("{asset}")  // {symbol}')
    log.info(
        f'await cprices.setGreenRefPoolConfig("{green_ref[0]}", '
        f'{green_ref_values[0]}n, {green_ref_values[1]}n, '
        f'{green_ref_values[2]}n, {green_ref_values[3]}n, '
        f'{green_ref_values[4]}n)'
    )
    log.info(
        f"await cprices.confirmGreenRefPoolConfig({len(curve_routes) + 1}n)"
    )

    log.info("// Confirm the remaining RipeHq replacements")
    for name, reg_id, _address in hq_updates:
        if reg_id != 7:
            log.info(
                f"await c.Ripe_RH_RipeHq.confirmAddressUpdateToRegistry("
                f"{reg_id}n)  // {name}"
            )
    log.info("// Confirm the Switchboard replacements")
    for name, reg_id, _address in switchboard_updates:
        log.info(
            f"await c.Ripe_RH_Switchboard.confirmAddressUpdateToRegistry("
            f"{reg_id}n)  // {name}"
        )
    log.info(f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{charlie.address}")')
    log.info(f'await charlie.pause("{teller.address}", false)  // unpause Teller')
    log.info("// Then run migration 2026082406 to authenticate and promote.")
