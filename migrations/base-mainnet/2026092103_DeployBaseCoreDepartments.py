"""Deploy inactive core department candidates. No vault deployments or funds moves."""

import boa

from scripts.utils import log
from scripts.utils.migration import Migration

HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
SUFFIX = "BaseDepartments20260921"


def migrate(migration: Migration):
    assert migration.chain() == "base-mainnet"
    hq = migration.get_contract("RipeHq")
    assert str(hq.address).lower() == HQ
    active = [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))]
    params = migration.blueprint().PARAMS
    assert params["CURVE_PRICES_ID"] == 2

    log.h1("1. Read live constructor configuration")
    endao = migration.get_contract("Endaoment", hq.getAddr(14))
    loot = migration.get_contract("Lootbox", hq.getAddr(16))
    deleverage = migration.get_contract("Deleverage", hq.getAddr(18))
    hr = migration.get_contract("HumanResources", hq.getAddr(15))
    bond = migration.get_contract("BondRoom", hq.getAddr(12))
    booster = migration.get_contract("BondBooster", bond.bondBooster())
    booster_config = (booster.maxBoostRatio(), booster.maxUnits(), booster.minLockDuration())
    loot_config = (loot.underscoreSendInterval(), loot.undyDepositRewardsAmount(), loot.undyYieldBonusAmount())
    dl_names = ("minDeleverageBps", "deleverageBuffer", "deleverageCooldown", "underscoreSafeSpreadBps")
    dl_config = tuple(getattr(deleverage, name)() for name in dl_names)
    # New fields absent from the legacy deployment; forgiveness stays disabled.
    dl_config += (10**15, 100, 0, 0)  # 0.001 GREEN payoff buffer, 1% overage

    log.h1("2. Deploy departments whose constructors only take HQ")
    new = {}
    for name in ("AuctionHouse", "AuctionHouseNFT", "Boardroom", "CreditRedeem", "TellerUtils", "EndaomentFunds"):
        new[name] = migration.deploy(name, hq.address, label=name + SUFFIX)

    log.h1("3. Deploy departments with live constructor parameters")
    new["BondBooster"] = migration.deploy("BondBooster", hq.address, *booster_config, label="BondBooster" + SUFFIX)
    new["BondRoom"] = migration.deploy("BondRoom", hq.address, new["BondBooster"].address, label="BondRoom" + SUFFIX)
    new["CreditEngine"] = migration.deploy("CreditEngine", hq.address, 2, label="CreditEngine" + SUFFIX)
    new["Endaoment"] = migration.deploy("Endaoment", hq.address, endao.WETH(), endao.ETH(), 2, label="Endaoment" + SUFFIX)
    new["HumanResources"] = migration.deploy(
        "HumanResources", hq.address, hr.minActionTimeLock(), hr.maxActionTimeLock(),
        label="HumanResources" + SUFFIX,
    )
    new["Lootbox"] = migration.deploy("Lootbox", hq.address, 43_200, *loot_config, label="Lootbox" + SUFFIX)
    new["Teller"] = migration.deploy("Teller", hq.address, True, 2, label="Teller" + SUFFIX)
    new["Deleverage"] = migration.deploy("Deleverage", hq.address, *dl_config, label="Deleverage" + SUFFIX)

    log.h1("4. Verify staged configuration; leave HQ and all custody untouched")
    assert new["HumanResources"].actionTimeLock() == 0
    assert new["Teller"].isPaused()
    assert new["BondRoom"].bondBooster() == new["BondBooster"].address
    assert tuple(getattr(new["BondBooster"], name)() for name in ("maxBoostRatio", "maxUnits", "minLockDuration")) == booster_config
    assert tuple(getattr(new["Lootbox"], name)() for name in ("underscoreSendInterval", "undyDepositRewardsAmount", "undyYieldBonusAmount")) == loot_config
    dl_names += ("deleverageFullPayoffBuffer", "deleverageOverageBps", "deleverageDustThreshold", "deleverageDustBps")
    assert tuple(getattr(new["Deleverage"], name)() for name in dl_names) == dl_config
    assert new["CreditEngine"].buybackRatio() == 0
    for name, candidate in new.items():
        assert 0 < len(boa.env.get_code(candidate.address)) <= 24_576
        log.info(f"STAGED {name}: {candidate.address}")
    assert [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))] == active
    log.info("NOT activation-ready: configure CreditEngine buybacks to 8000 (80%) during cutover.")
    log.info("Review other mutable policy/state and transfer EndaomentFunds before retiring old custody.")
    log.info("Teller remains paused. No timelocks enabled, HQ proposals sent, or funds moved.")
