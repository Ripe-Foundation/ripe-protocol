"""Deploy one fresh Robinhood protocol generation behind the existing RipeHq.

Retained on purpose: RipeHq, GreenToken, SavingsGreen, RipeToken, the two CCIP
token pools, GREEN/USDG, and RIPE/WETH.  Everything else in the active graph is
deployed again, including Ledger, MissionControl, all three child registries,
their vault/switchboard/price-source children, and all core departments.

Ledger and every vault start with empty user state.  DefaultsRobinhoodLive
preserves the reviewed global configuration and Ledger's ripeAvailFor* budgets;
it intentionally does not preserve per-user accounting.  Existing pools are
only referenced by the fresh price sources and are never deployed or funded.

The deployer temporarily governs each fresh configurable tree, builds it with
zero setup delay, and relinquishes local governance before the Safe activates
the roots.  HumanResources is deployed with no local governance already.
Candidate deployment itself changes no live RipeHq address.
"""

from pathlib import Path

from scripts.utils import log
from scripts.utils.ledger_deployment import validate_ledger_action_block_source
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    BOND_BOOSTER_MAX_BOOST_RATIO,
    BOND_BOOSTER_MAX_UNITS,
    BOND_BOOSTER_MIN_LOCK_DURATION,
    DELEVERAGE_BUFFER,
    DELEVERAGE_COOLDOWN,
    DELEVERAGE_DUST_BPS,
    DELEVERAGE_DUST_THRESHOLD,
    DELEVERAGE_FULL_PAYOFF_BUFFER,
    DELEVERAGE_MIN_BPS,
    DELEVERAGE_OVERAGE_BPS,
    DELEVERAGE_UNDERSCORE_SPREAD,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOCAL_GOV_MAX_TIMELOCK,
    LOCAL_GOV_MIN_TIMELOCK,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PSM_MAX_INTERVAL_MINT,
    PSM_MAX_INTERVAL_REDEEM,
    PSM_MINT_FEE,
    PSM_NUM_BLOCKS_PER_INTERVAL,
    PSM_REDEEM_FEE,
    PSM_YIELD_LEGO_ID,
    PSM_YIELD_VAULT_TOKEN,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    RIPE_WETH_POOL,
    STALE_WINDOW_DEFAULT,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)


RIPE_HQ = "RipeHq"
CANDIDATE_SUFFIX = "Candidate2026082100"
SNAPSHOT_BLOCK = 42_563_001
SNAPSHOT_BLOCK_HASH = (
    "0x9e99f47a4f3d7063150fe69b81e909865e299f61deae423118c15e4a3662ba42"
)

# Safe activation order. Ledger is first so no fresh vault generation can ever
# be observed with the old participation accounting, even inside the batch.
HQ_REPLACEMENTS = (
    ("Ledger", 4),
    ("MissionControl", 5),
    ("Switchboard", 6),
    ("PriceDesk", 7),
    ("VaultBook", 8),
    ("AuctionHouse", 9),
    ("AuctionHouseNFT", 10),
    ("Boardroom", 11),
    ("BondRoom", 12),
    ("CreditEngine", 13),
    ("Endaoment", 14),
    ("HumanResources", 15),
    ("Lootbox", 16),
    ("Teller", 17),
    ("Deleverage", 18),
    ("CreditRedeem", 19),
    ("TellerUtils", 20),
    ("EndaomentFunds", 21),
    ("EndaomentPSM", 22),
)

SWITCHBOARD_CHILDREN = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
    ("SwitchboardDelta", 4),
    ("SwitchboardEcho", 5),
)
PRICE_SOURCE_CHILDREN = (
    ("ChainlinkPrices", 1),
    ("CurvePrices", 2),
    ("UniswapV2Prices", 3),
)
VAULT_CHILDREN = (
    ("StabilityPool", 1),
    ("RipeGov", 2),
    ("SimpleErc20", 3),
)

# Read from the authenticated active CurvePrices constructor record.  This is
# a replacement dependency, not a new launch-time external selection.
LIVE_CURVE_ADDRESS_PROVIDER = "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648"


def candidate_label(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def _as_address(value):
    return str(getattr(value, "address", value)).lower()


def _require_snapshot_source():
    source = (
        Path(__file__).resolve().parents[2]
        / "contracts/config/DefaultsRobinhoodLive.vy"
    ).read_text()
    required = (
        f"#   snapshot block: {SNAPSHOT_BLOCK}",
        f"#   snapshot block hash: {SNAPSHOT_BLOCK_HASH}",
        "#   snapshot finality: verified against the provider finalized tag",
        "CONTRIB_TEMPLATE: immutable(address)",
    )
    if any(line not in source for line in required):
        raise RuntimeError("FULL_REDEPLOY_DEFAULTS_SNAPSHOT_MISMATCH")


def _assert_registry(registry, migration, entries, error_prefix):
    for name, reg_id in entries:
        if _as_address(registry.getAddr(reg_id)) != _as_address(
            migration.get_address(name)
        ):
            raise RuntimeError(f"{error_prefix}:{name}:{reg_id}")


def _assert_live_graph(migration, hq):
    _assert_registry(hq, migration, HQ_REPLACEMENTS, "FULL_REDEPLOY_HQ_MISMATCH")
    _assert_registry(
        migration.get_contract("Switchboard"),
        migration,
        SWITCHBOARD_CHILDREN,
        "FULL_REDEPLOY_SWITCHBOARD_MISMATCH",
    )
    _assert_registry(
        migration.get_contract("PriceDesk"),
        migration,
        PRICE_SOURCE_CHILDREN,
        "FULL_REDEPLOY_PRICE_DESK_MISMATCH",
    )
    _assert_registry(
        migration.get_contract("VaultBook"),
        migration,
        VAULT_CHILDREN,
        "FULL_REDEPLOY_VAULT_BOOK_MISMATCH",
    )


def _register(migration, registry, contract, name, expected_id):
    migration.execute(registry.startAddNewAddressToRegistry, contract, name)
    actual = int(migration.execute(registry.confirmNewAddressToRegistry, contract))
    assert actual == expected_id, f"{name} registered at {actual}, expected {expected_id}"


def _relinquish_gov(migration, contract):
    """Remove the deployer's temporary local governance."""
    current = _as_address(contract.governance())
    assert current in (_as_address(migration.account()), ZERO_ADDRESS)
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: _as_address(contract.governance()) == ZERO_ADDRESS,
    )
    assert _as_address(contract.governance()) == ZERO_ADDRESS


def _is_nft(config):
    if hasattr(config, "isNft"):
        return bool(config.isNft)
    return bool(config[-1])


def _asset_label(asset):
    """Best-effort ERC-20 symbol for readable deployment output."""
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
    text = str(asset)
    return f"{text[:8]}…{text[-6:]}"


def _chainlink_route_matches(chainlink, asset, expected):
    actual = chainlink.feedConfig(asset)
    return (
        _as_address(actual[0]) == _as_address(expected[0])
        and int(actual[1]) == int(expected[1])
        and bool(actual[2]) == bool(expected[2])
        and bool(actual[3]) == bool(expected[3])
        and int(actual[4]) == int(expected[4])
    )


def _sync_fungible_scales(migration, price_desk, active_mc, eth, usdg):
    eth = _as_address(eth)
    synced = set()
    for index in range(1, int(active_mc.numAssets())):
        asset = active_mc.assets(index)
        low = _as_address(asset)
        if low in (ZERO_ADDRESS, eth) or _is_nft(active_mc.assetConfig(asset)):
            continue
        migration.execute(price_desk.syncTokenScale, asset)
        assert int(price_desk.tokenScale(asset)) != 0
        synced.add(low)
    if _as_address(usdg) not in synced:
        migration.execute(price_desk.syncTokenScale, usdg)
        assert int(price_desk.tokenScale(usdg)) != 0


def migrate(migration: Migration):
    log.h1("Full fresh-generation preflight")
    _require_snapshot_source()
    hq = migration.get_contract(RIPE_HQ)
    _assert_live_graph(migration, hq)
    deployer = migration.account()
    active_price_desk = migration.get_contract("PriceDesk")
    active_chainlink = migration.get_contract("ChainlinkPrices")
    active_curve = migration.get_contract("CurvePrices")
    active_endaoment = migration.get_contract("Endaoment")
    active_psm = migration.get_contract("EndaomentPSM")
    eth = active_price_desk.ETH()
    weth = active_chainlink.WETH()
    btc = active_chainlink.BTC()
    eth_feed = active_chainlink.feedConfig(eth)[0]
    btc_feed = active_chainlink.feedConfig(btc)[0]
    usdg = active_psm.USDC()
    assert _as_address(active_endaoment.WETH()) == _as_address(weth)
    assert _as_address(active_endaoment.ETH()) == _as_address(eth)

    core_chainlink_assets = {
        _as_address(weth),
        _as_address(eth),
        _as_address(btc),
    }
    chainlink_routes = []
    for asset in active_chainlink.getPricedAssets():
        if _as_address(asset) in core_chainlink_assets:
            continue
        config = active_chainlink.feedConfig(asset)
        assert _as_address(config[0]) != ZERO_ADDRESS
        chainlink_routes.append(
            (
                _asset_label(asset),
                asset,
                config[0],
                int(config[4]),
                bool(config[2]),
                bool(config[3]),
            )
        )

    curve_routes = []
    for asset in active_curve.getPricedAssets():
        config = active_curve.curveConfig(asset)
        assert _as_address(config[0]) != ZERO_ADDRESS
        curve_routes.append((_asset_label(asset), asset, config[0]))
    green_ref = active_curve.greenRefPoolConfig()
    assert _as_address(green_ref[0]) != ZERO_ADDRESS
    green_ref_config = (
        int(green_ref[5]),
        int(green_ref[6]),
        int(green_ref[7]),
        int(green_ref[8]),
        int(green_ref[9]),
    )
    log.info("Retaining RipeHq, tokens, CCIP pools, GREEN/USDG, and RIPE/WETH.")
    log.info("Deploying 33 contracts; Ledger and all vault user state start empty.")

    # This is initcode used by future Contributor clones, not an active contract
    # with its own registry slot.  MissionControl activation is what selects it.
    log.h1("Deploying live defaults and accounting")
    contributor = migration.deploy_bp("Contributor")
    defaults = migration.deploy(
        "DefaultsRobinhoodLive",
        contributor,
        label=candidate_label("DefaultsRobinhoodLive"),
    )
    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
        label=candidate_label("Ledger"),
    )
    validation = validate_ledger_action_block_source(
        migration,
        ledger.address,
        LEDGER_ACTION_BLOCK_SOURCE,
        allow_local_preview=True,
    )
    if validation is None:
        log.info("Ledger ArbSys validation skipped for the local/fork preview.")
    else:
        source, action_block = validation
        log.info(f"Ledger action source: 0x{source:040x}; ArbSys block: {action_block}")

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
        label=candidate_label("MissionControl"),
    )

    log.h1("Building fresh Switchboard tree")
    switchboard = migration.deploy(
        "Switchboard",
        hq,
        deployer,
        LOCAL_GOV_MIN_TIMELOCK,
        LOCAL_GOV_MAX_TIMELOCK,
        label=candidate_label("Switchboard"),
    )
    boards = []
    for name, reg_id in SWITCHBOARD_CHILDREN:
        args = [hq, deployer]
        if name == "SwitchboardAlpha":
            args.extend((STALE_WINDOW_MIN, STALE_WINDOW_MAX))
        args.extend((SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK))
        board = migration.deploy(name, *args, label=candidate_label(name))
        _register(migration, switchboard, board, name, reg_id)
        boards.append(board)
    for board in boards:
        _relinquish_gov(migration, board)
    _relinquish_gov(migration, switchboard)

    log.h1("Building fresh PriceDesk tree")
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
        STALE_WINDOW_DEFAULT,
        label=candidate_label("ChainlinkPrices"),
    )
    for symbol, asset, feed, stale_time, needs_eth, needs_btc in chainlink_routes:
        log.info(f"Adding Chainlink route {symbol:<5} -> {feed}")
        migration.execute(
            chainlink.addNewPriceFeed,
            asset,
            feed,
            stale_time,
            needs_eth,
            needs_btc,
        )
        expected = (feed, int(active_chainlink.feedConfig(asset)[1]), needs_eth, needs_btc, stale_time)
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
        migration.get_address("GreenToken"),
        migration.get_address("SavingsGreen"),
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
        label=candidate_label("CurvePrices"),
    )
    # Current CurvePrices qualifies itself through the PriceDesk selected by
    # RipeHq. The live PriceDesk predates qualifyCallerPriceSource(), so these
    # routes are configured by the Safe immediately after it confirms the new
    # PriceDesk root.
    assert int(curve.actionId()) == 1
    assert int(curve.actionTimeLock()) == 0
    _register(migration, price_desk, curve, "CurvePrices", 2)

    uniswap = migration.deploy(
        "UniswapV2Prices",
        hq,
        RIPE_WETH_POOL,
        migration.get_address("RipeToken"),
        weth,
        label=candidate_label("UniswapV2Prices"),
    )
    assert uniswap.isMonitoringOnly()
    _register(migration, price_desk, uniswap, "UniswapV2Prices", 3)
    _sync_fungible_scales(
        migration,
        price_desk,
        migration.get_contract("MissionControl"),
        eth,
        usdg,
    )
    _relinquish_gov(migration, chainlink)
    _relinquish_gov(migration, curve)
    _relinquish_gov(migration, price_desk)

    log.h1("Building fresh VaultBook tree")
    vault_book = migration.deploy(
        "VaultBook",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate_label("VaultBook"),
    )
    for name, reg_id in VAULT_CHILDREN:
        vault = migration.deploy(name, hq, label=candidate_label(name))
        _register(migration, vault_book, vault, name, reg_id)
    _relinquish_gov(migration, vault_book)

    updates = [
        ("Ledger", 4, ledger.address),
        ("MissionControl", 5, mission_control.address),
        ("Switchboard", 6, switchboard.address),
        ("PriceDesk", 7, price_desk.address),
        ("VaultBook", 8, vault_book.address),
    ]

    def redeploy(name, reg_id, *args):
        contract = migration.deploy(name, *args, label=candidate_label(name))
        updates.append((name, reg_id, contract.address))
        return contract

    log.h1("Deploying fresh core departments")
    redeploy("AuctionHouse", 9, hq)
    redeploy("AuctionHouseNFT", 10, hq)
    redeploy("Boardroom", 11, hq)
    bond_booster = migration.deploy(
        "BondBooster",
        hq,
        BOND_BOOSTER_MAX_BOOST_RATIO,
        BOND_BOOSTER_MAX_UNITS,
        BOND_BOOSTER_MIN_LOCK_DURATION,
        label=candidate_label("BondBooster"),
    )
    redeploy("BondRoom", 12, hq, bond_booster)
    redeploy("CreditEngine", 13, hq)
    redeploy("Endaoment", 14, hq, weth, eth)
    human_resources = redeploy(
        "HumanResources", 15, hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK
    )
    redeploy(
        "Lootbox",
        16,
        hq,
        LOOTBOX_MIN_SEND_INTERVAL,
        LOOTBOX_SEND_INTERVAL,
        LOOTBOX_DEPOSIT_REWARD,
        LOOTBOX_YIELD_BONUS,
    )
    redeploy("Teller", 17, hq, False)
    redeploy(
        "Deleverage",
        18,
        hq,
        DELEVERAGE_MIN_BPS,
        DELEVERAGE_BUFFER,
        DELEVERAGE_COOLDOWN,
        DELEVERAGE_UNDERSCORE_SPREAD,
        DELEVERAGE_FULL_PAYOFF_BUFFER,
        DELEVERAGE_OVERAGE_BPS,
        DELEVERAGE_DUST_THRESHOLD,
        DELEVERAGE_DUST_BPS,
    )
    redeploy("CreditRedeem", 19, hq)
    redeploy("TellerUtils", 20, hq)
    redeploy("EndaomentFunds", 21, hq)
    redeploy(
        "EndaomentPSM",
        22,
        hq,
        PSM_NUM_BLOCKS_PER_INTERVAL,
        PSM_MINT_FEE,
        PSM_MAX_INTERVAL_MINT,
        PSM_REDEEM_FEE,
        PSM_MAX_INTERVAL_REDEEM,
        active_psm.USDC(),
        PSM_YIELD_LEGO_ID,
        PSM_YIELD_VAULT_TOKEN,
    )

    assert int(human_resources.actionTimeLock()) == 0
    assert int(human_resources.minActionTimeLock()) == HR_MIN_TIMELOCK
    assert _as_address(human_resources.governance()) == ZERO_ADDRESS
    green_ref_action_id = len(curve_routes) + 1

    log.h1("Safe activation plan")
    hq_delay = int(hq.registryChangeTimeLock())
    log.info(f"Safe: {hq.governance()}")
    log.info(f"RipeHq registry delay: {hq_delay} blocks")
    log.info(" ID  Contract             Fresh address")
    log.info(" --  -------------------  ------------------------------------------")
    for name, reg_id, candidate in updates:
        assert _as_address(hq.getAddr(reg_id)) != _as_address(candidate)
        log.info(f" {reg_id:>2}  {name:<19}  {candidate}")

    curve_call_count = 2 * len(curve_routes) + 2
    if hq_delay == 0:
        log.h2(f"Submit one atomic Safe batch — {38 + curve_call_count} calls")
        log.info("1. Start all 19 RipeHq updates in the table order")
        log.info("2. Confirm PriceDesk (HQ id 7) first")
        log.info(f"3. Execute the {curve_call_count} CurvePrices calls below")
        log.info("4. Confirm the other 18 RipeHq updates in table order")
    else:
        log.h2("Safe batch 1 — start all 19 RipeHq updates")
        log.info(f"Wait {hq_delay} RipeHq blocks after batch 1.")
        log.h2("Safe batch 2 — PriceDesk, Curve setup, then remaining confirmations")

    log.h2("RipeHq calls")
    for name, reg_id, candidate in updates:
        log.info(f"startAddressUpdateToRegistry({reg_id}, {candidate})  # {name}")
    log.info("confirmAddressUpdateToRegistry(7)  # PriceDesk first")

    log.h2("CurvePrices calls after PriceDesk confirmation")
    log.info(f"CurvePrices setup target: {curve.address}")
    for symbol, asset, pool in curve_routes:
        log.info(f"addNewPriceFeed({asset}, {pool})  # {symbol}")
        log.info(f"confirmNewPriceFeed({asset})  # {symbol}")
    log.info(
        "setGreenRefPoolConfig("
        f"{green_ref[0]}, {', '.join(str(value) for value in green_ref_config)})"
    )
    log.info(f"confirmGreenRefPoolConfig({green_ref_action_id})")

    log.h2("Remaining RipeHq confirmations")
    for name, reg_id, _candidate in updates:
        if reg_id != 7:
            log.info(f"confirmAddressUpdateToRegistry({reg_id})  # {name}")

    log.h2("After Safe activation")
    log.info("Run migration 2026082101 to authenticate and promote all candidates.")
