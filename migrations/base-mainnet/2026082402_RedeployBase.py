"""Stage the complete Base replacement generation.

Read ``migrate`` from top to bottom as the deployment checklist.  RipeHq,
tokens, CCIP pools, liquidity pools, Ledger, and the five funded source vaults
remain in place.  The replacement VaultBook keeps those source vaults at ids
1-5 and appends five fresh migration targets at ids 6-10.

This migration only deploys candidates.  It prints the Safe calls that start
and confirm the RipeHq changes; it never changes the live registry itself.
Vault positions are moved later through SwitchboardEcho and VaultMigrator.
"""

from pathlib import Path

from scripts.utils import log
from scripts.utils.migration import Migration


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
CANDIDATE_SUFFIX = "Candidate2026082402"

# Retained Base deployment.  These are deliberately independent of the
# manifest because the manifest contains unpromoted historical candidates.
RIPE_HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
LEDGER = "0x365256e322a47Aa2015F6724783F326e9B24fA47"
GREEN = "0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707"
SAVINGS_GREEN = "0xaa0f13488CE069A7B5a099457c753A7CFBE04d36"
RIPE = "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0"
GREEN_POOL = "0xd6c283655B42FA0eb2685F7AB819784F071459dc"
RIPE_WETH_POOL = "0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9"
RIPE_CCIP_POOL = "0x6E3f8465aF365a2C400C361783ea51ad44b3C836"
GREEN_CCIP_POOL = "0xEF56E5036728718Baa577257Ff4FA9259E9e895f"

ACTIVE_MISSION_CONTROL = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
ACTIVE_SWITCHBOARD = "0x20Fb680786004902DaCa00b1070B32F070716Cab"
ACTIVE_PRICE_DESK = "0x2F7901BE53cC94AEF174f1a0764430840360Ef53"
ACTIVE_VAULT_BOOK = "0xB758e30C14825519b895Fd9928d5d8748A71a944"

ACTIVE_CHAINLINK = "0xD11B23b6391e294DF49961E64231bddDE5bB5E89"
ACTIVE_CURVE = "0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d"
ACTIVE_PYTH = "0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98"
ACTIVE_STORK = "0xceE8Ed804f72b6EcB6B2D679ca17B545bD654bF6"
ACTIVE_AERO = "0x5ce2BbD5eBe9f7d9322a8F56740F95b9576eE0A2"
ACTIVE_WSUPER_OETH = "0x064488f53849616eeE3EE32c29307922B319bb7C"
ACTIVE_UNDY = "0x64D0F785c3D4bf4675f4b8432D765175F014A8Ac"
ACTIVE_REDSTONE = "0x9f20F25f037046721A292B19A486932ef390EAf9"

# The funded source vaults never move or change id during activation.
SOURCE_VAULTS = (
    ("StabilityPool source", 1, "0x2a157096af6337b2b4bd47de435520572ed5a439"),
    ("RipeGov source", 2, "0xe42b3dC546527EB70D741B185Dc57226cA01839D"),
    ("SimpleErc20 source", 3, "0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD"),
    ("RebaseErc20 source", 4, "0xce2E96C9F6806731914A7b4c3E4aC1F296d98597"),
    ("Underscore source", 5, "0x4549A368c00f803862d457C4C0c659a293F26C66"),
)

# Base block/timestamp policy.
REGISTRY_MIN_DELAY = 3_600
REGISTRY_MAX_DELAY = 302_400
ACTION_MIN_DELAY = 3_600
ACTION_MAX_DELAY = 302_400
STALE_TIME_MIN = 5 * 60
STALE_TIME_MAX = 7 * 24 * 60 * 60
DEFAULT_STALE_TIME = 24 * 60 * 60
PYTH_PRICES_ID = 4
CURVE_PRICES_ID = 2

# Constructor values retained from the active Base generation.
BOND_BOOSTER_ARGS = (20_000, 25_000, 7_776_000)
LOOTBOX_ARGS = (43_200, 43_200, 25 * 10**18, 150 * 10**18)
DELEVERAGE_ARGS = (0, 0, 0, 100, 10**15, 100, 0, 0)
PSM_ARGS = (
    43_200,
    0,
    20_000 * 10**18,
    0,
    100_000 * 10**18,
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    13,
    "0x99e65176F7FA8743E3fbaEF277d1Da448e361367",
)

# Base external dependencies.
ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
WETH = "0x4200000000000000000000000000000000000006"
BTC = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"
CURVE_ADDRESS_PROVIDER = "0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98"
MORPHO_FACTORIES = (
    "0xFf62A7c278C62eD665133147129245053Bbf5918",
    "0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101",
)
EULER_FACTORIES = (
    "0x7F321498A801A191a93C840750ed637149dDf8D0",
    "0x72bbDB652F2AEC9056115644EfCcDd1986F51f15",
)
FLUID_RESOLVER = "0x3aF6FBEc4a2FE517F56E402C65e3f4c3e18C1D86"
COMPOUND_V3_CONFIGURATOR = "0x45939657d1CA34A8FA39A924B71D28Fe8431e581"
MOONWELL_COMPTROLLER = "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C"
AAVE_V3_ADDRESS_PROVIDER = "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"

def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Bind the live Base generation and snapshot its oracle routes.
    # ------------------------------------------------------------------
    log.h1("1. Reading the retained Base deployment")
    _require_defaults_snapshot()

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    assert _address(hq.getAddr(1)) == _address(GREEN)
    assert _address(hq.getAddr(2)) == _address(SAVINGS_GREEN)
    assert _address(hq.getAddr(3)) == _address(RIPE)
    assert _address(hq.getAddr(4)) == _address(LEDGER)
    assert _address(hq.getAddr(5)) == _address(ACTIVE_MISSION_CONTROL)
    assert _address(hq.getAddr(6)) == _address(ACTIVE_SWITCHBOARD)
    assert _address(hq.getAddr(7)) == _address(ACTIVE_PRICE_DESK)
    assert _address(hq.getAddr(8)) == _address(ACTIVE_VAULT_BOOK)
    assert _address(hq.getAddr(23)) == _address(RIPE_CCIP_POOL)
    assert _address(hq.getAddr(24)) == _address(GREEN_CCIP_POOL)
    assert _address(hq.getAddr(25)) == ZERO_ADDRESS

    old_vault_book = migration.get_contract("VaultBook", ACTIVE_VAULT_BOOK)
    assert int(old_vault_book.numAddrs()) == 6
    for _name, vault_id, vault_address in SOURCE_VAULTS:
        assert _address(old_vault_book.getAddr(vault_id)) == _address(vault_address)

    old_chainlink = migration.get_contract("ChainlinkPrices", ACTIVE_CHAINLINK)
    old_curve = migration.get_contract("CurvePrices", ACTIVE_CURVE)
    old_pyth = migration.get_contract("PythPrices", ACTIVE_PYTH)
    old_stork = migration.get_contract("StorkPrices", ACTIVE_STORK)
    old_undy = migration.get_contract("UndyVaultPrices", ACTIVE_UNDY)
    old_redstone = migration.get_contract("RedStone", ACTIVE_REDSTONE)

    curve_routes = [
        (asset, old_curve.curveConfig(asset).pool)
        for asset in old_curve.getPricedAssets()
    ]
    green_ref = old_curve.greenRefPoolConfig()

    # ------------------------------------------------------------------
    # 2. Deploy live defaults and the replacement MissionControl.
    # ------------------------------------------------------------------
    log.h1("2. Deploying live defaults and MissionControl")
    contributor = migration.deploy_bp("Contributor")
    defaults = migration.deploy(
        "DefaultsBaseLive",
        contributor,
        label=candidate("DefaultsBaseLive"),
    )
    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
        label=candidate("MissionControl"),
    )

    # ------------------------------------------------------------------
    # 3. Build a fresh Switchboard tree.
    # ------------------------------------------------------------------
    log.h1("3. Deploying Switchboard and its five children")
    deployer = migration.account()
    switchboard = migration.deploy(
        "Switchboard",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("Switchboard"),
    )
    alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        deployer,
        STALE_TIME_MIN,
        STALE_TIME_MAX,
        ACTION_MIN_DELAY,
        ACTION_MAX_DELAY,
        PYTH_PRICES_ID,
        label=candidate("SwitchboardAlpha"),
    )
    bravo = migration.deploy(
        "SwitchboardBravo", hq, deployer, ACTION_MIN_DELAY, ACTION_MAX_DELAY,
        label=candidate("SwitchboardBravo"),
    )
    charlie = migration.deploy(
        "SwitchboardCharlie", hq, deployer, ACTION_MIN_DELAY, ACTION_MAX_DELAY,
        label=candidate("SwitchboardCharlie"),
    )
    delta = migration.deploy(
        "SwitchboardDelta", hq, deployer, ACTION_MIN_DELAY, ACTION_MAX_DELAY,
        label=candidate("SwitchboardDelta"),
    )
    echo = migration.deploy(
        "SwitchboardEcho", hq, deployer, ACTION_MIN_DELAY, ACTION_MAX_DELAY,
        label=candidate("SwitchboardEcho"),
    )
    for name, board, board_id in (
        ("SwitchboardAlpha", alpha, 1),
        ("SwitchboardBravo", bravo, 2),
        ("SwitchboardCharlie", charlie, 3),
        ("SwitchboardDelta", delta, 4),
        ("SwitchboardEcho", echo, 5),
    ):
        _register(migration, switchboard, board, name, board_id)
        _relinquish(migration, board)
    _relinquish(migration, switchboard)

    # ------------------------------------------------------------------
    # 4. Build a fresh PriceDesk and clone every active live route.
    # ------------------------------------------------------------------
    log.h1("4. Deploying PriceDesk and price sources")
    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        deployer,
        ETH,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("PriceDesk"),
    )

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        WETH,
        ETH,
        BTC,
        old_chainlink.feedConfig(ETH).feed,
        old_chainlink.feedConfig(BTC).feed,
        DEFAULT_STALE_TIME,
        label=candidate("ChainlinkPrices"),
    )
    _copy_chainlink(migration, old_chainlink, chainlink)
    _register(migration, price_desk, chainlink, "ChainlinkPrices", 1)

    curve = migration.deploy(
        "CurvePrices",
        hq,
        deployer,
        CURVE_ADDRESS_PROVIDER,
        GREEN,
        SAVINGS_GREEN,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("CurvePrices"),
    )
    _register(migration, price_desk, curve, "CurvePrices", 2)

    # Slot 3 stays disabled, matching the live PriceDesk.  Deploying and then
    # disabling BlueChip preserves the registry numbering without re-enabling
    # a source governance already retired.
    bluechip = migration.deploy(
        "BlueChipYieldPrices",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        MORPHO_FACTORIES,
        EULER_FACTORIES,
        FLUID_RESOLVER,
        COMPOUND_V3_CONFIGURATOR,
        MOONWELL_COMPTROLLER,
        AAVE_V3_ADDRESS_PROVIDER,
        ZERO_ADDRESS,
        label=candidate("BlueChipYieldPrices"),
    )
    _register(migration, price_desk, bluechip, "BlueChipYieldPrices", 3)
    assert migration.execute(price_desk.startAddressDisableInRegistry, 3)
    assert migration.execute(price_desk.confirmAddressDisableInRegistry, 3)

    pyth = migration.deploy(
        "PythPrices", hq, deployer, old_pyth.PYTH(), REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY, label=candidate("PythPrices"),
    )
    _copy_bytes32_feeds(migration, old_pyth, pyth)
    _register(migration, price_desk, pyth, "PythPrices", 4)

    stork = migration.deploy(
        "StorkPrices", hq, deployer, old_stork.STORK(), REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY, label=candidate("StorkPrices"),
    )
    _copy_bytes32_feeds(migration, old_stork, stork)
    _register(migration, price_desk, stork, "StorkPrices", 5)

    aero = migration.deploy(
        "AeroRipePrices", hq, RIPE_WETH_POOL, RIPE, WETH,
        label=candidate("AeroRipePrices"),
    )
    assert aero.isMonitoringOnly()
    _register(migration, price_desk, aero, "AeroRipePrices", 6)

    old_wsuper = migration.get_contract("wsuperOETHbPrices", ACTIVE_WSUPER_OETH)
    wsuper = migration.deploy(
        "wsuperOETHbPrices",
        hq,
        old_wsuper.MCBETH(),
        old_wsuper.SUPER_OETH(),
        old_wsuper.WRAPPED_SUPER_OETH(),
        old_wsuper.VVV(),
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("wsuperOETHbPrices"),
    )
    _register(migration, price_desk, wsuper, "wsuperOETHbPrices", 7)

    undy = migration.deploy(
        "UndyVaultPrices", hq, deployer, REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY, label=candidate("UndyVaultPrices"),
    )
    _copy_undy(migration, old_undy, undy)
    _register(migration, price_desk, undy, "UndyVaultPrices", 8)

    redstone = migration.deploy(
        "RedStone", hq, deployer, old_redstone.ETH(), REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY, label=candidate("RedStone"),
    )
    _copy_redstone(migration, old_redstone, redstone)
    _register(migration, price_desk, redstone, "RedStone", 9)

    _sync_token_scales(migration, price_desk)
    for governed in (chainlink, curve, bluechip, pyth, stork, undy, redstone):
        _relinquish(migration, governed)
    _relinquish(migration, price_desk)

    # ------------------------------------------------------------------
    # 5. Keep source vault ids 1-5 and append fresh targets at ids 6-10.
    # ------------------------------------------------------------------
    log.h1("5. Deploying VaultBook and five migration targets")
    vault_book = migration.deploy(
        "VaultBook",
        hq,
        deployer,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=candidate("VaultBook"),
    )
    for name, vault_id, vault_address in SOURCE_VAULTS:
        source = migration.get_contract(_source_contract_name(vault_id), vault_address)
        _register(migration, vault_book, source, name, vault_id)

    stability_pool = migration.deploy(
        "StabilityPool", hq, label=candidate("StabilityPool")
    )
    ripe_gov = migration.deploy("RipeGov", hq, label=candidate("RipeGov"))
    simple = migration.deploy("SimpleErc20", hq, label=candidate("SimpleErc20"))
    rebase = migration.deploy("RebaseErc20", hq, label=candidate("RebaseErc20"))
    underscore = migration.deploy(
        "SimpleErc20", hq, label=candidate("UnderscoreVault")
    )
    for name, vault, vault_id in (
        ("StabilityPool target", stability_pool, 6),
        ("RipeGov target", ripe_gov, 7),
        ("SimpleErc20 target", simple, 8),
        ("RebaseErc20 target", rebase, 9),
        ("Underscore target", underscore, 10),
    ):
        _register(migration, vault_book, vault, name, vault_id)
    _relinquish(migration, vault_book)

    # ------------------------------------------------------------------
    # 6. Deploy every replaceable department.  Teller starts paused so no
    #    user path can cross the generation boundary before migration.
    # ------------------------------------------------------------------
    log.h1("6. Deploying departments and VaultMigrator")
    auction_house = migration.deploy(
        "AuctionHouse", hq, label=candidate("AuctionHouse")
    )
    auction_house_nft = migration.deploy(
        "AuctionHouseNFT", hq, label=candidate("AuctionHouseNFT")
    )
    boardroom = migration.deploy("Boardroom", hq, label=candidate("Boardroom"))
    bond_booster = migration.deploy(
        "BondBooster", hq, *BOND_BOOSTER_ARGS, label=candidate("BondBooster")
    )
    bond_room = migration.deploy(
        "BondRoom", hq, bond_booster, label=candidate("BondRoom")
    )
    credit_engine = migration.deploy(
        "CreditEngine", hq, CURVE_PRICES_ID, label=candidate("CreditEngine")
    )
    endaoment = migration.deploy(
        "Endaoment", hq, WETH, ETH, CURVE_PRICES_ID,
        label=candidate("Endaoment"),
    )
    human_resources = migration.deploy(
        "HumanResources", hq, ACTION_MIN_DELAY, ACTION_MAX_DELAY,
        label=candidate("HumanResources"),
    )
    lootbox = migration.deploy(
        "Lootbox", hq, *LOOTBOX_ARGS, label=candidate("Lootbox")
    )
    teller = migration.deploy(
        "Teller", hq, True, CURVE_PRICES_ID, label=candidate("Teller")
    )
    deleverage = migration.deploy(
        "Deleverage", hq, *DELEVERAGE_ARGS, label=candidate("Deleverage")
    )
    credit_redeem = migration.deploy(
        "CreditRedeem", hq, label=candidate("CreditRedeem")
    )
    teller_utils = migration.deploy(
        "TellerUtils", hq, label=candidate("TellerUtils")
    )
    endaoment_funds = migration.deploy(
        "EndaomentFunds", hq, label=candidate("EndaomentFunds")
    )
    endaoment_psm = migration.deploy(
        "EndaomentPSM", hq, *PSM_ARGS, label=candidate("EndaomentPSM")
    )
    vault_migrator = migration.deploy(
        "VaultMigrator",
        hq,
        False,
        SOURCE_VAULTS[1][2],
        label=candidate("VaultMigrator"),
    )

    replacements = (
        ("MissionControl", 5, mission_control),
        ("Switchboard", 6, switchboard),
        ("PriceDesk", 7, price_desk),
        ("VaultBook", 8, vault_book),
        ("AuctionHouse", 9, auction_house),
        ("AuctionHouseNFT", 10, auction_house_nft),
        ("Boardroom", 11, boardroom),
        ("BondRoom", 12, bond_room),
        ("CreditEngine", 13, credit_engine),
        ("Endaoment", 14, endaoment),
        ("HumanResources", 15, human_resources),
        ("Lootbox", 16, lootbox),
        ("Teller", 17, teller),
        ("Deleverage", 18, deleverage),
        ("CreditRedeem", 19, credit_redeem),
        ("TellerUtils", 20, teller_utils),
        ("EndaomentFunds", 21, endaoment_funds),
        ("EndaomentPSM", 22, endaoment_psm),
    )

    # ------------------------------------------------------------------
    # 7. Print the two Safe batches.  PriceDesk is confirmed first because
    #    CurvePrices validates each copied route through its active registry.
    # ------------------------------------------------------------------
    log.h1("7. Safe activation checklist")
    log.info("Batch 1 — start the 18 replacements and append VaultMigrator")
    for name, registry_id, contract in replacements:
        log.info(
            f'await c.Ripe_Base_RipeHq.startAddressUpdateToRegistry('
            f'{registry_id}n, "{contract.address}")  // {name}'
        )
    log.info(
        "await c.Ripe_Base_RipeHq.startAddNewAddressToRegistry("
        f'"{vault_migrator.address}", "VaultMigrator")'
    )

    log.info("Batch 2 — after the RipeHq registry delay")
    log.info("await c.Ripe_Base_RipeHq.confirmAddressUpdateToRegistry(7n)  // PriceDesk")
    log.info(
        f'const cprices = c.Ripe_Base_CurvePrices.at("{curve.address}")'
    )
    for asset, pool in curve_routes:
        log.info(f'await cprices.addNewPriceFeed("{asset}", "{pool}")')
        log.info(f'await cprices.confirmNewPriceFeed("{asset}")')
    log.info(
        "await cprices.setGreenRefPoolConfig("
        f'"{green_ref.pool}", {int(green_ref.maxNumSnapshots)}n, '
        f'{int(green_ref.dangerTrigger)}n, {int(green_ref.staleBlocks)}n, '
        f'{int(green_ref.stabilizerAdjustWeight)}n, '
        f'{int(green_ref.stabilizerMaxPoolDebt)}n)'
    )
    log.info(f"await cprices.confirmGreenRefPoolConfig({len(curve_routes) + 1}n)")
    for name, registry_id, _contract in replacements:
        if registry_id != 7:
            log.info(
                f"await c.Ripe_Base_RipeHq.confirmAddressUpdateToRegistry("
                f"{registry_id}n)  // {name}"
            )
    log.info(
        "await c.Ripe_Base_RipeHq.confirmNewAddressToRegistry("
        f'"{vault_migrator.address}")  // VaultMigrator, expected id 25'
    )
    log.info("Run migration 2026082403 only after every registry readback matches.")
    log.info("Teller remains paused until the vault migration is reconciled.")


# Small repetitive helpers keep the checklist above readable.


def _address(value):
    return str(getattr(value, "address", value)).lower()


def _require_defaults_snapshot():
    source = (
        Path(__file__).resolve().parents[2]
        / "contracts/config/DefaultsBaseLive.vy"
    ).read_text()
    required = (
        "#   snapshot block: 50413043",
        "#   snapshot block hash: 0xb8740bbfc9cae9c88d127951ce66e7348294304a1c8c376281c3f4c58ad52bc4",
        "#   snapshot finality: verified against the provider finalized tag",
        "CONTRIB_TEMPLATE: immutable(address)",
    )
    if any(value not in source for value in required):
        raise RuntimeError("BASE_DEFAULTS_SNAPSHOT_MISMATCH")


def _source_contract_name(vault_id):
    return {
        1: "StabilityPool",
        2: "RipeGov",
        3: "SimpleErc20",
        4: "RebaseErc20",
        5: "SimpleErc20",
    }[vault_id]


def _register(migration, registry, contract, name, expected_id):
    assert migration.execute(registry.startAddNewAddressToRegistry, contract, name)
    actual_id = int(migration.execute(registry.confirmNewAddressToRegistry, contract))
    assert actual_id == expected_id, f"{name}: expected id {expected_id}, got {actual_id}"


def _relinquish(migration, contract):
    if _address(contract.governance()) != ZERO_ADDRESS:
        migration.execute(contract.relinquishGov)
    assert _address(contract.governance()) == ZERO_ADDRESS


def _copy_chainlink(migration, old, new):
    core = {_address(WETH), _address(ETH), _address(BTC)}
    for asset in old.getPricedAssets():
        if _address(asset) in core:
            continue
        config = old.feedConfig(asset)
        assert migration.execute(
            new.addNewPriceFeed,
            asset,
            config.feed,
            int(config.staleTime),
            bool(config.needsEthToUsd),
            bool(config.needsBtcToUsd),
        )
        assert migration.execute(new.confirmNewPriceFeed, asset)


def _copy_bytes32_feeds(migration, old, new):
    for asset in old.getPricedAssets():
        config = old.feedConfig(asset)
        assert migration.execute(
            new.addNewPriceFeed, asset, config.feedId, int(config.staleTime)
        )
        assert migration.execute(new.confirmNewPriceFeed, asset)


def _copy_redstone(migration, old, new):
    for asset in old.getPricedAssets():
        config = old.feedConfig(asset)
        assert migration.execute(
            new.addNewPriceFeed,
            asset,
            config.feed,
            int(config.staleTime),
            bool(config.needsEthToUsd),
        )
        assert migration.execute(new.confirmNewPriceFeed, asset)


def _copy_undy(migration, old, new):
    for asset in old.getPricedAssets():
        config = old.priceConfigs(asset)
        assert migration.execute(
            new.addNewPriceFeed,
            asset,
            int(config.minSnapshotDelay),
            int(config.maxNumSnapshots),
            int(config.maxUpsideDeviation),
            int(config.staleTime),
        )
        assert migration.execute(new.confirmNewPriceFeed, asset)


def _sync_token_scales(migration, price_desk):
    mission_control = migration.get_contract("MissionControl", ACTIVE_MISSION_CONTROL)
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        config = mission_control.assetConfig(asset)
        is_nft = bool(config.isNft) if hasattr(config, "isNft") else bool(config[-1])
        if _address(asset) != _address(ETH) and not is_nft:
            migration.execute(price_desk.syncTokenScale, asset)
