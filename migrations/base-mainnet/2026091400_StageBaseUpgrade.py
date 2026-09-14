"""Deploy Base upgrade candidates only. Activation and funds migration happen later."""

import boa

from scripts.utils import log
from scripts.utils.migration import Migration


ZERO = "0x" + "00" * 20
SUFFIX = "BaseUpgradeCandidate20260914"
HQ_IDS = {
    "Ledger": 4, "MissionControl": 5, "Switchboard": 6, "PriceDesk": 7,
    "VaultBook": 8, "BondRoom": 12, "Endaoment": 14,
    "Lootbox": 16, "Deleverage": 18,
}


def migrate(migration: Migration):
    log.h1("1. Read the existing Base deployment")
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_UPGRADE_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    active = {}
    for name, slot in HQ_IDS.items():
        addr = hq.getAddr(slot)
        if address(addr) == ZERO:
            raise RuntimeError(f"BASE_UPGRADE_MISSING_ACTIVE:{name}")
        active[name] = migration.get_contract(name, addr)

    params = migration.blueprint().PARAMS
    min_lock = params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"]
    max_lock = params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    legacy_gov = active["VaultBook"].getAddr(2)
    if address(legacy_gov) == ZERO:
        raise RuntimeError("BASE_UPGRADE_MISSING_LEGACY_GOV")

    # Capture legacy constructor inputs before sending any deployments.
    old_lootbox = active["Lootbox"]
    send_interval = old_lootbox.underscoreSendInterval()
    deposit_rewards = old_lootbox.undyDepositRewardsAmount()
    yield_bonus = old_lootbox.undyYieldBonusAmount()
    old_deleverage = active["Deleverage"]
    min_deleverage_bps = old_deleverage.minDeleverageBps()
    deleverage_buffer = old_deleverage.deleverageBuffer()
    deleverage_cooldown = old_deleverage.deleverageCooldown()
    underscore_safe_spread = old_deleverage.underscoreSafeSpreadBps()
    weth = active["Endaoment"].WETH()
    eth = active["Endaoment"].ETH()
    old_booster = migration.get_contract("BondBooster", active["BondRoom"].bondBooster())
    max_boost_ratio = old_booster.maxBoostRatio()
    max_boost_units = old_booster.maxUnits()
    min_boost_lock = old_booster.minLockDuration()

    log.h1("2. Deploy Switchboard and its seven controllers")
    # No temporary deployer governance. Setup delays remain a cutover task.
    candidates = {}
    candidates["Switchboard"] = migration.deploy(
        "Switchboard", hq.address, ZERO, min_lock, max_lock,
        label=f"Switchboard{SUFFIX}",
    )
    candidates["SwitchboardAlpha"] = migration.deploy(
        "SwitchboardAlpha", hq.address, ZERO,
        params["PRICE_DESK_MIN_STALE_TIME"],
        params["PRICE_DESK_MAX_STALE_TIME"],
        min_lock, max_lock, params["PYTH_PRICES_ID"],
        label=f"SwitchboardAlpha{SUFFIX}",
    )
    candidates["SwitchboardBravo"] = migration.deploy(
        "SwitchboardBravo", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardBravo{SUFFIX}",
    )
    candidates["SwitchboardCharlie"] = migration.deploy(
        "SwitchboardCharlie", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardCharlie{SUFFIX}",
    )
    candidates["SwitchboardDelta"] = migration.deploy(
        "SwitchboardDelta", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardDelta{SUFFIX}",
    )
    candidates["SwitchboardEcho"] = migration.deploy(
        "SwitchboardEcho", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardEcho{SUFFIX}",
    )
    candidates["SwitchboardFoxtrot"] = migration.deploy(
        "SwitchboardFoxtrot", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardFoxtrot{SUFFIX}",
    )
    candidates["SwitchboardGolf"] = migration.deploy(
        "SwitchboardGolf", hq.address, ZERO, min_lock, max_lock,
        label=f"SwitchboardGolf{SUFFIX}",
    )

    log.h1("3. Deploy the empty vault registry and replacement vaults")
    candidates["VaultBook"] = migration.deploy(
        "VaultBook", hq.address, ZERO,
        params["VAULT_BOOK_MIN_REG_TIMELOCK"],
        params["VAULT_BOOK_MAX_REG_TIMELOCK"],
        label=f"VaultBook{SUFFIX}",
    )
    candidates["StabilityPool"] = migration.deploy(
        "StabilityPool", hq.address,
        label=f"StabilityPool{SUFFIX}",
    )
    candidates["RipeGov"] = migration.deploy(
        "RipeGov", hq.address,
        label=f"RipeGov{SUFFIX}",
    )
    candidates["SimpleErc20"] = migration.deploy(
        "SimpleErc20", hq.address,
        label=f"SimpleErc20{SUFFIX}",
    )
    candidates["RebaseErc20"] = migration.deploy(
        "RebaseErc20", hq.address,
        label=f"RebaseErc20{SUFFIX}",
    )
    # Separate instance for legacy vault 5, not the vault 3 replacement.
    candidates["UnderscoreVault"] = migration.deploy(
        "SimpleErc20", hq.address,
        label=f"UnderscoreVault{SUFFIX}",
    )
    # Start the migrator paused.
    candidates["VaultMigrator"] = migration.deploy(
        "VaultMigrator", hq.address, True, legacy_gov,
        label=f"VaultMigrator{SUFFIX}",
    )

    log.h1("4. Deploy the replacement departments")
    candidates["AuctionHouse"] = migration.deploy(
        "AuctionHouse", hq.address,
        label=f"AuctionHouse{SUFFIX}",
    )
    candidates["AuctionHouseNFT"] = migration.deploy(
        "AuctionHouseNFT", hq.address,
        label=f"AuctionHouseNFT{SUFFIX}",
    )
    candidates["Boardroom"] = migration.deploy(
        "Boardroom", hq.address,
        label=f"Boardroom{SUFFIX}",
    )
    candidates["CreditRedeem"] = migration.deploy(
        "CreditRedeem", hq.address,
        label=f"CreditRedeem{SUFFIX}",
    )
    candidates["TellerUtils"] = migration.deploy(
        "TellerUtils", hq.address,
        label=f"TellerUtils{SUFFIX}",
    )
    candidates["EndaomentFunds"] = migration.deploy(
        "EndaomentFunds", hq.address,
        label=f"EndaomentFunds{SUFFIX}",
    )
    candidates["BondBooster"] = migration.deploy(
        "BondBooster", hq.address, max_boost_ratio, max_boost_units, min_boost_lock,
        label=f"BondBooster{SUFFIX}",
    )
    candidates["BondRoom"] = migration.deploy(
        "BondRoom", hq.address, candidates["BondBooster"].address,
        label=f"BondRoom{SUFFIX}",
    )
    candidates["CreditEngine"] = migration.deploy(
        "CreditEngine", hq.address, params["CURVE_PRICES_ID"],
        label=f"CreditEngine{SUFFIX}",
    )
    candidates["HumanResources"] = migration.deploy(
        "HumanResources", hq.address, min_lock, max_lock,
        label=f"HumanResources{SUFFIX}",
    )
    candidates["Lootbox"] = migration.deploy(
        "Lootbox", hq.address, 1, send_interval, deposit_rewards, yield_bonus,
        label=f"Lootbox{SUFFIX}",
    )
    # Start Teller paused.
    candidates["Teller"] = migration.deploy(
        "Teller", hq.address, True, params["CURVE_PRICES_ID"],
        label=f"Teller{SUFFIX}",
    )
    candidates["Deleverage"] = migration.deploy(
        "Deleverage", hq.address,
        min_deleverage_bps,
        deleverage_buffer,
        deleverage_cooldown,
        underscore_safe_spread,
        10**15,  # new field: 0.001 GREEN full-payoff buffer
        100,     # new field: 1% overage
        0,       # new field: dust forgiveness threshold disabled
        0,       # new field: dust forgiveness BPS disabled
        label=f"Deleverage{SUFFIX}",
    )
    candidates["Endaoment"] = migration.deploy(
        "Endaoment", hq.address, weth, eth, params["CURVE_PRICES_ID"],
        label=f"Endaoment{SUFFIX}",
    )

    log.h1("5. Check candidates and confirm active addresses are unchanged")
    for name, candidate in candidates.items():
        size = len(boa.env.get_code(candidate.address))
        if not 0 < size <= 24576:
            raise RuntimeError(f"BASE_UPGRADE_RUNTIME_SIZE:{name}:{size}")
        log.info(f"STAGED ONLY {name}: {candidate.address}")
    for name, slot in HQ_IDS.items():
        if address(hq.getAddr(slot)) != address(active[name]):
            raise RuntimeError(f"BASE_UPGRADE_ACTIVE_ADDRESS_CHANGED:{name}")

    log.info("Deployment complete. No registrations, vault IDs assigned, or funds moved.")


def address(value):
    return str(getattr(value, "address", value)).lower()
