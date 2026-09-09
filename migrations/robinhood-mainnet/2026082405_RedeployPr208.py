"""Redeploy the Robinhood contracts changed by PR #208.

Read ``migrate`` from top to bottom as the deployment checklist.  RipeHq,
tokens, CCIP pools, Ledger, MissionControl, UniswapV2Prices, RipeGov, and
SimpleErc20 remain in place.  This step deploys eleven replacements and prints
the Safe calls that activate them.  It never changes the live registries.

The small helpers below ``migrate`` only make transactions safe to resume and
keep repetitive registry/readback code out of the checklist.
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

# Retained generation, verified directly from RipeHq and PriceDesk on RH mainnet.
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
RETAINED_SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
RETAINED_PRICE_DESK = "0x4EEc14F2905ec6bCfE9f399b90c1b92128B0AF8B"
RETAINED_CHAINLINK_PRICES = "0x599180f6cFCDa61FcFDC924c637b97d41c007E0F"
RETAINED_CURVE_PRICES = "0xC98e6c6CD0DDF20aA71413Ee12A1d169f58C418E"
RETAINED_VAULT_BOOK = "0x1f90ef42Da9B41502d2311300E13FAcf70c64be7"

HQ_UPDATES = (
    ("PriceDesk", 7),
    ("VaultBook", 8),
    ("CreditEngine", 13),
    ("Endaoment", 14),
    ("Teller", 17),
)
SWITCHBOARD_UPDATES = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
)


def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    # ---------------------------------------------------------------------
    # 1. Read the retained live deployment.
    # ---------------------------------------------------------------------
    log.h1("1. Reading retained Robinhood contracts")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", RETAINED_SWITCHBOARD)
    old_price_desk = migration.get_contract("PriceDesk", RETAINED_PRICE_DESK)
    old_chainlink = migration.get_contract(
        "ChainlinkPrices", RETAINED_CHAINLINK_PRICES
    )
    old_curve = migration.get_contract("CurvePrices", RETAINED_CURVE_PRICES)
    old_vault_book = migration.get_contract("VaultBook", RETAINED_VAULT_BOOK)
    mission_control = migration.get_contract("MissionControl")
    endaoment_psm = migration.get_contract("EndaomentPSM")

    require_registry(hq, migration, HQ_UPDATES)
    require_registry(switchboard, migration, SWITCHBOARD_UPDATES)
    require_registry(
        old_price_desk,
        migration,
        (("ChainlinkPrices", 1), ("CurvePrices", 2), ("UniswapV2Prices", 3)),
    )
    require_registry(
        old_vault_book,
        migration,
        (("StabilityPool", 1), ("RipeGov", 2), ("SimpleErc20", 3)),
    )

    deployer = migration.account()
    eth = old_price_desk.ETH()
    weth = old_chainlink.WETH()
    btc = old_chainlink.BTC()
    usdg = endaoment_psm.USDC()
    green = migration.get_address("GreenToken")
    savings_green = migration.get_address("SavingsGreen")

    chainlink_routes = read_chainlink_routes(old_chainlink, eth, weth, btc)
    curve_routes = read_curve_routes(old_curve, green)
    green_ref_pool = old_curve.greenRefPoolConfig()

    # ---------------------------------------------------------------------
    # 2. Deploy a fresh PriceDesk tree and copy the live oracle routes.
    # ---------------------------------------------------------------------
    log.h1("2. Deploying PriceDesk and price sources")

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        deployer,
        eth,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("PriceDesk"),
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
        old_chainlink.feedConfig(eth)[0],
        old_chainlink.feedConfig(btc)[0],
        STALE_WINDOW_INHERIT,
        label=candidate("ChainlinkPrices"),
    )
    require_core_chainlink_routes(chainlink, old_chainlink, eth, weth, btc)
    copy_chainlink_routes(migration, chainlink, chainlink_routes)
    register(migration, price_desk, chainlink, "ChainlinkPrices", 1)

    curve = migration.deploy(
        "CurvePrices",
        hq,
        deployer,
        LIVE_CURVE_ADDRESS_PROVIDER,
        green,
        savings_green,
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
        label=candidate("CurvePrices"),
    )
    register(migration, price_desk, curve, "CurvePrices", 2)

    # UniswapV2Prices did not change, so keep the existing monitor at id 3.
    register(
        migration,
        price_desk,
        migration.get_contract("UniswapV2Prices"),
        "UniswapV2Prices",
        3,
    )
    sync_token_scales(migration, price_desk, mission_control, eth, usdg)

    relinquish_governance(migration, chainlink)
    relinquish_governance(migration, curve)
    relinquish_governance(migration, price_desk)

    # ---------------------------------------------------------------------
    # 3. Deploy a fresh VaultBook tree.
    # ---------------------------------------------------------------------
    log.h1("3. Deploying VaultBook and StabilityPool")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("VaultBook"),
    )
    stability_pool = migration.deploy(
        "StabilityPool",
        hq,
        label=candidate("StabilityPool"),
    )
    register(migration, vault_book, stability_pool, "StabilityPool", 1)

    # These two vaults did not change and remain registered at ids 2 and 3.
    register(migration, vault_book, migration.get_contract("RipeGov"), "RipeGov", 2)
    register(
        migration,
        vault_book,
        migration.get_contract("SimpleErc20"),
        "SimpleErc20",
        3,
    )
    relinquish_governance(migration, vault_book)

    # ---------------------------------------------------------------------
    # 4. Deploy the three changed Switchboards.
    # ---------------------------------------------------------------------
    log.h1("4. Deploying Switchboard Alpha, Bravo, and Charlie")

    alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        deployer,
        STALE_WINDOW_MIN,
        STALE_WINDOW_MAX,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        PYTH_PRICES_ID,
        label=candidate("SwitchboardAlpha"),
    )
    bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        deployer,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=candidate("SwitchboardBravo"),
    )
    charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        deployer,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=candidate("SwitchboardCharlie"),
    )
    relinquish_governance(migration, alpha)
    relinquish_governance(migration, bravo)
    relinquish_governance(migration, charlie)

    # ---------------------------------------------------------------------
    # 5. Deploy the three changed departments.
    # ---------------------------------------------------------------------
    log.h1("5. Deploying CreditEngine, Endaoment, and Teller")

    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
        CURVE_PRICES_ID,
        label=candidate("CreditEngine"),
    )
    endaoment = migration.deploy(
        "Endaoment",
        hq,
        weth,
        eth,
        CURVE_PRICES_ID,
        label=candidate("Endaoment"),
    )
    teller = migration.deploy(
        "Teller",
        hq,
        TELLER_SHOULD_PAUSE,
        CURVE_PRICES_ID,
        label=candidate("Teller"),
    )
    assert bool(teller.isPaused()) is TELLER_SHOULD_PAUSE

    # ---------------------------------------------------------------------
    # 6. Print the Safe batch. The migration does not submit these calls.
    # ---------------------------------------------------------------------
    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0

    print_safe_batch(
        hq_updates=(
            ("PriceDesk", 7, price_desk.address),
            ("VaultBook", 8, vault_book.address),
            ("CreditEngine", 13, credit_engine.address),
            ("Endaoment", 14, endaoment.address),
            ("Teller", 17, teller.address),
        ),
        switchboard_updates=(
            ("SwitchboardAlpha", 1, alpha.address),
            ("SwitchboardBravo", 2, bravo.address),
            ("SwitchboardCharlie", 3, charlie.address),
        ),
        curve=curve,
        curve_routes=curve_routes,
        green_ref_pool=green_ref_pool,
        charlie=charlie,
        teller=teller,
    )


# -------------------------------------------------------------------------
# Repetitive deployment mechanics
# -------------------------------------------------------------------------


def address(value):
    return str(getattr(value, "address", value)).lower()


def require_registry(registry, migration, entries):
    for name, reg_id in entries:
        expected = migration.get_address(name)
        actual = registry.getAddr(reg_id)
        if address(actual) != address(expected):
            raise RuntimeError(f"PR208_ACTIVE_SLOT_MISMATCH:{name}:{reg_id}")


def register(migration, registry, contract, name, expected_id):
    def registration_started():
        if int(registry.getRegId(contract)) == expected_id:
            return True
        pending = registry.pendingNewAddr(contract)
        return str(pending[0]) == name and int(pending[2]) != 0

    assert migration.execute_reconciled(
        registry.startAddNewAddressToRegistry,
        registration_started,
        contract,
        name,
    )
    assert migration.execute_reconciled(
        registry.confirmNewAddressToRegistry,
        lambda: int(registry.getRegId(contract)) == expected_id,
        contract,
    )
    assert int(registry.getRegId(contract)) == expected_id


def relinquish_governance(migration, contract):
    assert address(contract.governance()) in (address(migration.account()), ZERO_ADDRESS)
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: address(contract.governance()) == ZERO_ADDRESS,
    )
    assert address(contract.governance()) == ZERO_ADDRESS


def chainlink_config(config, stale_time=None):
    return (
        address(config[0]),
        int(config[1]),
        bool(config[2]),
        bool(config[3]),
        int(config[4] if stale_time is None else stale_time),
    )


def read_chainlink_routes(chainlink, eth, weth, btc):
    core_assets = {address(eth), address(weth), address(btc)}
    routes = []
    for asset in chainlink.getPricedAssets():
        if address(asset) in core_assets:
            continue
        active = chainlink.feedConfig(asset)
        routes.append(
            (
                token_label(asset),
                asset,
                chainlink_config(active, stale_time_override_for_asset(str(asset))),
            )
        )
    return routes


def require_core_chainlink_routes(fresh, old, eth, weth, btc):
    for asset in (eth, weth, btc):
        expected = chainlink_config(old.feedConfig(asset), STALE_WINDOW_INHERIT)
        assert chainlink_config(fresh.feedConfig(asset)) == expected


def copy_chainlink_routes(migration, chainlink, routes):
    for symbol, asset, expected in routes:
        def route_is_live(asset=asset, expected=expected):
            return chainlink_config(chainlink.feedConfig(asset)) == expected

        def route_is_pending_or_live(asset=asset, expected=expected):
            if route_is_live(asset, expected):
                return True
            pending = chainlink.pendingUpdates(asset)
            return int(pending[0]) != 0 and chainlink_config(pending[1]) == expected

        log.info(f"Copying Chainlink route {symbol} (stale override {expected[4]})")
        assert migration.execute_reconciled(
            chainlink.addNewPriceFeed,
            route_is_pending_or_live,
            asset,
            expected[0],
            expected[4],
            expected[2],
            expected[3],
        )
        assert migration.execute_reconciled(
            chainlink.confirmNewPriceFeed,
            route_is_live,
            asset,
        )


def read_curve_routes(curve, green):
    routes = [
        (token_label(asset), asset, curve.curveConfig(asset)[0])
        for asset in curve.getPricedAssets()
    ]
    routes.sort(key=lambda route: address(route[1]) != address(green))
    return routes


def is_nft(config):
    return bool(config.isNft) if hasattr(config, "isNft") else bool(config[-1])


def sync_token_scales(migration, price_desk, mission_control, eth, usdg):
    eth = address(eth)
    synced = set()
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        normalized = address(asset)
        if normalized in (ZERO_ADDRESS, eth):
            continue
        if is_nft(mission_control.assetConfig(asset)):
            continue
        assert migration.execute_reconciled(
            price_desk.syncTokenScale,
            lambda asset=asset: int(price_desk.tokenScale(asset)) != 0,
            asset,
        )
        synced.add(normalized)

    if address(usdg) not in synced:
        assert migration.execute_reconciled(
            price_desk.syncTokenScale,
            lambda: int(price_desk.tokenScale(usdg)) != 0,
            usdg,
        )


def token_label(asset):
    """Return a token symbol for the operator-facing Safe plan when possible."""
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


def print_safe_batch(
    *,
    hq_updates,
    switchboard_updates,
    curve,
    curve_routes,
    green_ref_pool,
    charlie,
    teller,
):
    log.h1("6. Safe batch — activate and configure the new generation")

    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(
        f'const switchboard = c.Ripe_RH_Switchboard.at("{RETAINED_SWITCHBOARD}")'
    )

    log.info("// Start the five RipeHq updates")
    for name, reg_id, contract_address in hq_updates:
        log.info(
            f'await hq.startAddressUpdateToRegistry('
            f'{reg_id}n, "{contract_address}")  // {name}'
        )

    log.info("// Start the three Switchboard updates")
    for name, reg_id, contract_address in switchboard_updates:
        log.info(
            f'await switchboard.startAddressUpdateToRegistry('
            f'{reg_id}n, "{contract_address}")  // {name}'
        )

    # CurvePrices resolves PriceDesk through RipeHq, so activate PriceDesk first.
    log.info("// Activate PriceDesk, then copy its Curve routes")
    log.info("await hq.confirmAddressUpdateToRegistry(7n)  // PriceDesk")
    log.info(f'const cprices = c.Ripe_RH_CurvePrices.at("{curve.address}")')
    for symbol, asset, pool in curve_routes:
        log.info(f'await cprices.addNewPriceFeed("{asset}", "{pool}")  // {symbol}')
        log.info(f'await cprices.confirmNewPriceFeed("{asset}")  // {symbol}')

    values = tuple(int(green_ref_pool[index]) for index in range(5, 10))
    log.info(
        f'await cprices.setGreenRefPoolConfig("{green_ref_pool[0]}", '
        f"{values[0]}n, {values[1]}n, {values[2]}n, {values[3]}n, {values[4]}n)"
    )
    log.info(f"await cprices.confirmGreenRefPoolConfig({len(curve_routes) + 1}n)")

    log.info("// Activate the remaining RipeHq contracts")
    for name, reg_id, _contract_address in hq_updates:
        if reg_id != 7:
            log.info(
                f"await hq.confirmAddressUpdateToRegistry("
                f"{reg_id}n)  // {name}"
            )

    log.info("// Activate the three Switchboards")
    for name, reg_id, _contract_address in switchboard_updates:
        log.info(
            f"await switchboard.confirmAddressUpdateToRegistry("
            f"{reg_id}n)  // {name}"
        )

    # Teller is intentionally constructed paused and unpaused only after the
    # fresh Charlie is canonical.
    log.info("// Unpause the new Teller through the new SwitchboardCharlie")
    log.info(f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{charlie.address}")')
    log.info(f'await charlie.pause("{teller.address}", false)')
    log.info("// Then run migration 2026082406 to authenticate and promote.")
