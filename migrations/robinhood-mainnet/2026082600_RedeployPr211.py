"""Stage the Robinhood contracts whose deployed runtime changes in PR #211.

Read ``migrate`` from top to bottom as the deployment checklist.  Nothing in
this migration changes a live registry.  It deploys the replacement contracts,
copies the live Chainlink routes, and prints the one Safe batch that activates
the reviewed generation.

The old Stability Pool contains real user funds today.  Governance has chosen
withdrawal rather than position migration, so an economically empty old pool
is a hard precondition.  VaultBook slot 1 is replaced only after every share,
underlying amount, and claim liability reads zero.
"""

from pathlib import Path

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    STALE_WINDOW_INHERIT,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


# This stays False while PR #211's Vyper files are still changing.  Final review
# must refresh the runtime inventory and Defaults snapshot before enabling it.
DEPLOYMENT_READY = False
PR211_REVIEW_HEAD = "b03ff2ba2d641ffcc17b365c6f4f299f69649c4e"
DEFAULTS_SNAPSHOT_BLOCK = 0
DEFAULTS_SNAPSHOT_BLOCK_HASH = ""
# Defaults cannot carry MissionControl.userConfig/userDelegation.  Final review
# must scan both Teller and SwitchboardCharlie events through the snapshot block.
USER_STATE_AUDIT_BLOCK = 0
USER_CONFIG_EVENT_COUNT = None
USER_DELEGATION_EVENT_COUNT = None

STAGED_SUFFIX = "Staged2026082600"

# Retained live generation.  Hardcoding makes reruns independent of accidental
# canonical-manifest edits and makes the review surface explicit.
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
LEDGER = "0xF1CD5BE4288b744913d33F55370793ca833D08d7"
MISSION_CONTROL = "0xD335373E59cA2F07FC3B779F2B456972C7EfDb29"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
SWITCHBOARD_BRAVO = "0x5281175B0f4a8ba4839d43d778434F7274Be52B8"
SWITCHBOARD_CHARLIE = "0x846176B2294a5168a04345087f0474738B569150"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
CHAINLINK_PRICES = "0xf4AF744784fBdB5f251F95a789AC0f9aB702d310"
VAULT_BOOK = "0x9B37ea4E5b250Fef242fFC88364A143Fa39DF090"
STABILITY_POOL = "0x03b9d0C5f628671FC877f267cC706BEd91Cc42fB"
AUCTION_HOUSE = "0xA5801c426590F44Bc7d33551Caf7354488C8516C"
CREDIT_ENGINE = "0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98"
HUMAN_RESOURCES = "0xCd9F242a2B82387a3ED02cC4a8a0fF9a7EE8d8F5"
TELLER = "0xceE8Ed804f72b6EcB6B2D679ca17B545bD654bF6"
DELEVERAGE = "0x781a37a5999760c73c52fcdE1a6A34668D8eA311"
CREDIT_REDEEM = "0x7aAB69c238EA051Fa9e8370559FD917a72dBe074"

HQ_UPDATES = (
    ("MissionControl", 5),
    ("AuctionHouse", 9),
    ("CreditEngine", 13),
    ("HumanResources", 15),
    ("Teller", 17),
    ("Deleverage", 18),
    ("CreditRedeem", 19),
)


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Bind the retained live generation and the final review inputs.
    # ------------------------------------------------------------------
    log.h1("1. PR #211 deployment preflight")
    require_release_inputs()

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    ledger = migration.get_contract("Ledger", LEDGER)
    old_mc = migration.get_contract("MissionControl", MISSION_CONTROL)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    old_bravo = migration.get_contract("SwitchboardBravo", SWITCHBOARD_BRAVO)
    charlie = migration.get_contract("SwitchboardCharlie", SWITCHBOARD_CHARLIE)
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    old_chainlink = migration.get_contract("ChainlinkPrices", CHAINLINK_PRICES)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    old_pool = migration.get_contract("StabilityPool", STABILITY_POOL)
    old_credit = migration.get_contract("CreditEngine", CREDIT_ENGINE)
    old_hr = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    old_deleverage = migration.get_contract("Deleverage", DELEVERAGE)

    require_slot(hq, 4, ledger)
    require_slot(hq, 5, old_mc)
    require_slot(hq, 9, AUCTION_HOUSE)
    require_slot(hq, 13, old_credit)
    require_slot(hq, 15, old_hr)
    require_slot(hq, 17, TELLER)
    require_slot(hq, 18, old_deleverage)
    require_slot(hq, 19, CREDIT_REDEEM)
    require_slot(switchboard, 2, old_bravo)
    require_slot(switchboard, 3, charlie)
    require_slot(price_desk, 1, old_chainlink)
    require_slot(vault_book, 1, old_pool)

    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0
    assert int(price_desk.registryChangeTimeLock()) == 0
    assert int(vault_book.registryChangeTimeLock()) == 0
    assert int(ledger.numContributors()) == 0
    assert int(old_hr.actionId()) == 1
    assert int(old_bravo.actionId()) == 1
    assert int(old_credit.undyVaulDiscount()) == 5_000
    assert int(old_credit.buybackRatio()) == 0
    require_empty_stability_pool(old_pool)

    # ------------------------------------------------------------------
    # 2. Deploy fresh live defaults and the changed PR #211 runtimes.
    # ------------------------------------------------------------------
    log.h1("2. Deploying the staged PR #211 generation")

    # Contributor is a blueprint rather than a registry member.  The fresh
    # Defaults contract binds it into MissionControl.hrConfig.
    contributor = migration.deploy_bp("Contributor")
    defaults = migration.deploy(
        "DefaultsRobinhoodLive",
        contributor,
        label=staged("DefaultsRobinhoodLive"),
    )

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
        label=staged("MissionControl"),
    )
    assert equivalent_global_config(old_mc, mission_control)
    assert as_address(mission_control.hrConfig()[0]) == as_address(contributor)

    bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=staged("SwitchboardBravo"),
    )
    relinquish_governance(migration, bravo)

    chainlink = deploy_chainlink_copy(migration, hq, old_chainlink)

    stability_pool = migration.deploy(
        "StabilityPool",
        hq,
        label=staged("StabilityPool"),
    )
    require_empty_stability_pool(stability_pool)

    auction_house = migration.deploy(
        "AuctionHouse", hq, label=staged("AuctionHouse")
    )
    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
        CURVE_PRICES_ID,
        label=staged("CreditEngine"),
    )
    human_resources = migration.deploy(
        "HumanResources",
        hq,
        HR_MIN_TIMELOCK,
        HR_MAX_TIMELOCK,
        label=staged("HumanResources"),
    )
    teller = migration.deploy(
        "Teller",
        hq,
        TELLER_SHOULD_PAUSE,
        CURVE_PRICES_ID,
        label=staged("Teller"),
    )
    deleverage = migration.deploy(
        "Deleverage",
        hq,
        *deleverage_config(old_deleverage),
        label=staged("Deleverage"),
    )
    credit_redeem = migration.deploy(
        "CreditRedeem", hq, label=staged("CreditRedeem")
    )

    assert int(credit_engine.undyVaulDiscount()) == int(old_credit.undyVaulDiscount())
    assert int(credit_engine.buybackRatio()) == int(old_credit.buybackRatio())
    assert as_address(human_resources.governance()) == ZERO_ADDRESS
    assert int(human_resources.actionTimeLock()) == 0
    assert bool(teller.isPaused()) is TELLER_SHOULD_PAUSE

    # ------------------------------------------------------------------
    # 3. Print the atomic Safe activation for team review.
    # ------------------------------------------------------------------
    log.h1("3. Safe activation batch")
    print_safe_batch(
        mission_control=mission_control,
        auction_house=auction_house,
        credit_engine=credit_engine,
        human_resources=human_resources,
        teller=teller,
        deleverage=deleverage,
        credit_redeem=credit_redeem,
        bravo=bravo,
        chainlink=chainlink,
        stability_pool=stability_pool,
        charlie=charlie,
    )


# ----------------------------------------------------------------------
# Repetitive readback and copy mechanics
# ----------------------------------------------------------------------


def as_address(value):
    return str(getattr(value, "address", value)).lower()


def require_release_inputs():
    if not DEPLOYMENT_READY:
        raise RuntimeError("PR211_DEPLOYMENT_NOT_FINAL")
    if DEFAULTS_SNAPSHOT_BLOCK == 0 or not DEFAULTS_SNAPSHOT_BLOCK_HASH:
        raise RuntimeError("PR211_DEFAULTS_SNAPSHOT_NOT_PINNED")
    if USER_STATE_AUDIT_BLOCK != DEFAULTS_SNAPSHOT_BLOCK:
        raise RuntimeError("PR211_USER_STATE_AUDIT_NOT_PINNED")
    if USER_CONFIG_EVENT_COUNT != 0 or USER_DELEGATION_EVENT_COUNT != 0:
        raise RuntimeError("PR211_MISSION_CONTROL_USER_STATE_NOT_EMPTY")

    source = (
        Path(__file__).resolve().parents[2]
        / "contracts/config/DefaultsRobinhoodLive.vy"
    ).read_text()
    required = (
        f"#   snapshot block: {DEFAULTS_SNAPSHOT_BLOCK}",
        f"#   snapshot block hash: {DEFAULTS_SNAPSHOT_BLOCK_HASH}",
        "#   snapshot finality: verified against the provider finalized tag",
        "CONTRIB_TEMPLATE: immutable(address)",
    )
    if any(marker not in source for marker in required):
        raise RuntimeError("PR211_DEFAULTS_SNAPSHOT_MISMATCH")


def require_slot(registry, reg_id, expected):
    if as_address(registry.getAddr(reg_id)) != as_address(expected):
        raise RuntimeError(f"PR211_ACTIVE_SLOT_MISMATCH:{reg_id}")


def require_empty_stability_pool(pool):
    for index in range(1, int(pool.numAssets())):
        asset = pool.vaultAssets(index)
        if int(pool.totalBalances(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_SHARES_REMAIN:{asset}")
        if int(pool.getTotalAmountForVault(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_FUNDS_REMAIN:{asset}")
        if int(pool.getNumActiveClaimAssets(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_ACTIVE_CLAIMS:{asset}")
        for claim_index in range(1, int(pool.numClaimableAssets(asset))):
            claim_asset = pool.claimableAssets(asset, claim_index)
            if int(pool.totalClaimableBalances(claim_asset)) != 0:
                raise RuntimeError(
                    f"PR211_STABILITY_POOL_CLAIM_LIABILITY:{claim_asset}"
                )


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def equivalent_global_config(old, fresh):
    scalar_getters = (
        "genConfig",
        "genDebtConfig",
        "hrConfig",
        "ripeBondConfig",
        "rewardsConfig",
        "getPriorityLiqAssetVaults",
        "getPriorityStabVaults",
        "getPriorityPriceSourceIds",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "coreRipeGovVaultId",
        "preferredStabVaultId",
        "totalPointsAllocs",
    )
    if any(normalized(getattr(old, name)()) != normalized(getattr(fresh, name)())
           for name in scalar_getters if name != "hrConfig"):
        return False

    # hrConfig differs only in the intentionally replaced Contributor template.
    if normalized(old.hrConfig()[1:]) != normalized(fresh.hrConfig()[1:]):
        return False

    old_assets = tuple(old.assets(i) for i in range(1, int(old.numAssets())))
    fresh_assets = tuple(fresh.assets(i) for i in range(1, int(fresh.numAssets())))
    if tuple(map(as_address, old_assets)) != tuple(map(as_address, fresh_assets)):
        return False
    for asset in old_assets:
        if normalized(old.assetConfig(asset)) != normalized(fresh.assetConfig(asset)):
            return False
        if normalized(old.ripeGovVaultConfig(asset)) != normalized(
            fresh.ripeGovVaultConfig(asset)
        ):
            return False

    old_signers = tuple(
        old.liteSigners(index) for index in range(1, int(old.numLiteSigners()))
    )
    fresh_signers = tuple(
        fresh.liteSigners(index)
        for index in range(1, int(fresh.numLiteSigners()))
    )
    if tuple(map(as_address, old_signers)) != tuple(map(as_address, fresh_signers)):
        return False

    # RH currently has three registered vault rows; both historical classifiers
    # must survive the MissionControl replacement exactly.
    for vault_id in range(1, 4):
        if bool(old.isStabVaultId(vault_id)) != bool(
            fresh.isStabVaultId(vault_id)
        ):
            return False
        if bool(old.isRipeGovVaultId(vault_id)) != bool(
            fresh.isRipeGovVaultId(vault_id)
        ):
            return False
    return True


def chainlink_config(value):
    return (
        as_address(value[0]),
        int(value[1]),
        bool(value[2]),
        bool(value[3]),
        int(value[4]),
    )


def deploy_chainlink_copy(migration, hq, old):
    eth = old.ETH()
    weth = old.WETH()
    btc = old.BTC()
    fresh = migration.deploy(
        "ChainlinkPrices",
        hq,
        migration.account(),
        PRICE_MIN_TIMELOCK,
        PRICE_MAX_TIMELOCK,
        weth,
        eth,
        btc,
        old.feedConfig(eth)[0],
        old.feedConfig(btc)[0],
        STALE_WINDOW_INHERIT,
        label=staged("ChainlinkPrices"),
    )

    core = {as_address(asset) for asset in (eth, weth, btc)}
    for asset in old.getPricedAssets():
        expected = chainlink_config(old.feedConfig(asset))
        if as_address(asset) in core:
            assert chainlink_config(fresh.feedConfig(asset)) == expected
            continue

        assert migration.execute_reconciled(
            fresh.addNewPriceFeed,
            lambda asset=asset, expected=expected: (
                int(fresh.pendingUpdates(asset)[0]) != 0
                or chainlink_config(fresh.feedConfig(asset)) == expected
            ),
            asset,
            expected[0],
            expected[4],
            expected[2],
            expected[3],
        )
        assert migration.execute_reconciled(
            fresh.confirmNewPriceFeed,
            lambda asset=asset, expected=expected: (
                chainlink_config(fresh.feedConfig(asset)) == expected
            ),
            asset,
        )

    assert tuple(map(as_address, fresh.getPricedAssets())) == tuple(
        map(as_address, old.getPricedAssets())
    )
    relinquish_governance(migration, fresh)
    return fresh


def relinquish_governance(migration, contract):
    assert as_address(contract.governance()) in (
        as_address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: as_address(contract.governance()) == ZERO_ADDRESS,
    )
    assert as_address(contract.governance()) == ZERO_ADDRESS


def deleverage_config(contract):
    return (
        int(contract.minDeleverageBps()),
        int(contract.deleverageBuffer()),
        int(contract.deleverageCooldown()),
        int(contract.underscoreSafeSpreadBps()),
        int(contract.deleverageFullPayoffBuffer()),
        int(contract.deleverageOverageBps()),
        int(contract.deleverageDustThreshold()),
        int(contract.deleverageDustBps()),
    )


def print_safe_batch(**fresh):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(f'const switchboard = c.Ripe_RH_Switchboard.at("{SWITCHBOARD}")')
    log.info(f'const priceDesk = c.Ripe_RH_PriceDesk.at("{PRICE_DESK}")')
    log.info(f'const vaultBook = c.Ripe_RH_VaultBook.at("{VAULT_BOOK}")')
    log.info("")

    log.info("// Start the seven RipeHq replacements")
    for name, reg_id in HQ_UPDATES:
        contract = fresh[camel_to_key(name)]
        log.info(
            f'await hq.startAddressUpdateToRegistry({reg_id}n, '
            f'"{contract.address}")  // {name}'
        )

    log.info("// Start the three child-registry replacements")
    log.info(
        "await switchboard.startAddressUpdateToRegistry(2n, "
        f'"{fresh["bravo"].address}")  // SwitchboardBravo'
    )
    log.info(
        "await priceDesk.startAddressUpdateToRegistry(1n, "
        f'"{fresh["chainlink"].address}")  // ChainlinkPrices'
    )
    log.info(
        "await vaultBook.startAddressUpdateToRegistry(1n, "
        f'"{fresh["stability_pool"].address}")  // StabilityPool'
    )
    log.info("")

    log.info("// Confirm every staged contract in dependency order")
    for name, reg_id in HQ_UPDATES:
        log.info(f"await hq.confirmAddressUpdateToRegistry({reg_id}n)  // {name}")
    log.info(
        "await switchboard.confirmAddressUpdateToRegistry(2n)  // SwitchboardBravo"
    )
    log.info("await priceDesk.confirmAddressUpdateToRegistry(1n)  // ChainlinkPrices")
    log.info("await vaultBook.confirmAddressUpdateToRegistry(1n)  // StabilityPool")
    log.info("")

    log.info("// Teller was deployed paused; reopen it only after activation")
    log.info(
        f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{fresh["charlie"].address}")'
    )
    log.info(f'await charlie.pause("{fresh["teller"].address}", false)')
    log.info("")
    log.info("// Then run migration 2026082601 to authenticate and promote.")


def camel_to_key(name):
    return {
        "MissionControl": "mission_control",
        "AuctionHouse": "auction_house",
        "CreditEngine": "credit_engine",
        "HumanResources": "human_resources",
        "Teller": "teller",
        "Deleverage": "deleverage",
        "CreditRedeem": "credit_redeem",
    }[name]
