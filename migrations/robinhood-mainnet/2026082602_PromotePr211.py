"""Verify and publish the activated clean PR #211 generation.

This migration sends no transaction. It checks registry readbacks,
constructors, the fresh VaultBook, and the copied Chainlink routes before
publishing canonical manifest names.
"""

from scripts.utils import log
from scripts.utils.ledger_deployment import validate_ledger_action_block_source
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PYTH_PRICES_ID,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


STAGED_SUFFIX = "Staged2026082600"

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
VAULT_BOOK_STAGED = "VaultBookStaged2026082601"

OLD_CHAINLINK_PRICES = "0xf4AF744784fBdB5f251F95a789AC0f9aB702d310"
OLD_DELEVERAGE = "0x781a37a5999760c73c52fcdE1a6A34668D8eA311"

SOURCE = {
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
    "Ledger": "contracts/data/Ledger.vy",
    "MissionControl": "contracts/data/MissionControl.vy",
    "SwitchboardAlpha": "contracts/config/SwitchboardAlpha.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "SwitchboardDelta": "contracts/config/SwitchboardDelta.vy",
    "ChainlinkPrices": "contracts/priceSources/ChainlinkPrices.vy",
    "VaultBook": "contracts/registries/VaultBook.vy",
    "StabilityPool": "contracts/vaults/StabilityPool.vy",
    "RipeGov": "contracts/vaults/RipeGov.vy",
    "AuctionHouse": "contracts/core/AuctionHouse.vy",
    "CreditEngine": "contracts/core/CreditEngine.vy",
    "HumanResources": "contracts/core/HumanResources.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "Teller": "contracts/core/Teller.vy",
    "Deleverage": "contracts/core/Deleverage.vy",
    "CreditRedeem": "contracts/core/CreditRedeem.vy",
}


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Read the staged generation and the retained registry roots.
    # ------------------------------------------------------------------
    log.h1("1. Reading the activated clean PR #211 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    vault_book = migration.get_contract(VAULT_BOOK_STAGED)

    defaults = migration.get_contract(staged("DefaultsRobinhoodLive"))
    contributor = migration.get_contract("Contributor")
    ledger = migration.get_contract(staged("Ledger"))
    mission_control = migration.get_contract(staged("MissionControl"))
    alpha = migration.get_contract(staged("SwitchboardAlpha"))
    bravo = migration.get_contract(staged("SwitchboardBravo"))
    charlie = migration.get_contract(staged("SwitchboardCharlie"))
    delta = migration.get_contract(staged("SwitchboardDelta"))
    chainlink = migration.get_contract(staged("ChainlinkPrices"))
    stability_pool = migration.get_contract(staged("StabilityPool"))
    ripe_gov = migration.get_contract(staged("RipeGov"))
    auction_house = migration.get_contract(staged("AuctionHouse"))
    credit_engine = migration.get_contract(staged("CreditEngine"))
    human_resources = migration.get_contract(staged("HumanResources"))
    lootbox = migration.get_contract(staged("Lootbox"))
    teller = migration.get_contract(staged("Teller"))
    deleverage = migration.get_contract(staged("Deleverage"))
    credit_redeem = migration.get_contract(staged("CreditRedeem"))

    # ------------------------------------------------------------------
    # 2. Prove activation and copied configuration.
    # ------------------------------------------------------------------
    log.h1("2. Checking registry and state readbacks")

    require_slot(hq, 4, ledger)
    require_slot(hq, 5, mission_control)
    require_slot(hq, 8, vault_book)
    require_slot(hq, 9, auction_house)
    require_slot(hq, 13, credit_engine)
    require_slot(hq, 15, human_resources)
    require_slot(hq, 16, lootbox)
    require_slot(hq, 17, teller)
    require_slot(hq, 18, deleverage)
    require_slot(hq, 19, credit_redeem)
    require_slot(switchboard, 1, alpha)
    require_slot(switchboard, 2, bravo)
    require_slot(switchboard, 3, charlie)
    require_slot(switchboard, 4, delta)
    require_slot(price_desk, 1, chainlink)
    require_slot(vault_book, 1, stability_pool)
    require_slot(vault_book, 2, ripe_gov)

    assert as_address(mission_control.hrConfig()[0]) == as_address(contributor)
    for board in (alpha, bravo, charlie, delta):
        assert as_address(board.governance()) == ZERO_ADDRESS
        assert int(board.actionTimeLock()) == 0
    assert as_address(chainlink.governance()) == ZERO_ADDRESS
    assert int(chainlink.actionTimeLock()) == 0
    assert as_address(human_resources.governance()) == ZERO_ADDRESS
    assert int(human_resources.actionTimeLock()) == 0
    assert not bool(teller.isPaused())
    assert int(credit_engine.undyVaulDiscount()) == 5_000
    assert int(credit_engine.buybackRatio()) == 0

    validate_ledger_action_block_source(
        migration,
        ledger.address,
        LEDGER_ACTION_BLOCK_SOURCE,
        allow_local_preview=True,
    )
    old_chainlink = migration.get_contract("ChainlinkPrices", OLD_CHAINLINK_PRICES)
    require_chainlink_copy(old_chainlink, chainlink)

    old_deleverage = migration.get_contract("Deleverage", OLD_DELEVERAGE)
    assert deleverage_config(deleverage) == deleverage_config(old_deleverage)

    # ------------------------------------------------------------------
    # 3. Authenticate constructors and publish canonical manifest names.
    # ------------------------------------------------------------------
    log.h1("3. Publishing the clean PR #211 manifest records")

    deployer = migration.account()
    eth = old_chainlink.ETH()
    weth = old_chainlink.WETH()
    btc = old_chainlink.BTC()
    default_stale_time = int(old_chainlink.feedConfig(eth)[4])
    promotions = (
        PromotionSpec(
            canonical_name="DefaultsRobinhoodLive",
            expected_source_path=SOURCE["DefaultsRobinhoodLive"],
            candidate_label=staged("DefaultsRobinhoodLive"),
            registry_name="RipeHq",
            registry=hq,
            registry_id=5,
            expected_constructor_args=(contributor,),
            activation_candidate_label=staged("MissionControl"),
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, defaults),
        ),
        promotion(
            "Ledger",
            "RipeHq",
            hq,
            4,
            (hq, defaults, LEDGER_ACTION_BLOCK_SOURCE),
        ),
        promotion("MissionControl", "RipeHq", hq, 5, (hq, defaults)),
        promotion(
            "SwitchboardAlpha",
            "Switchboard",
            switchboard,
            1,
            (
                hq,
                deployer,
                STALE_WINDOW_MIN,
                STALE_WINDOW_MAX,
                SWITCHBOARD_MIN_TIMELOCK,
                SWITCHBOARD_MAX_TIMELOCK,
                PYTH_PRICES_ID,
            ),
        ),
        promotion(
            "SwitchboardBravo",
            "Switchboard",
            switchboard,
            2,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "SwitchboardCharlie",
            "Switchboard",
            switchboard,
            3,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "SwitchboardDelta",
            "Switchboard",
            switchboard,
            4,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "ChainlinkPrices",
            "PriceDesk",
            price_desk,
            1,
            (
                hq,
                deployer,
                PRICE_MIN_TIMELOCK,
                PRICE_MAX_TIMELOCK,
                weth,
                eth,
                btc,
                old_chainlink.feedConfig(eth)[0],
                old_chainlink.feedConfig(btc)[0],
                default_stale_time,
            ),
        ),
        PromotionSpec(
            canonical_name="VaultBook",
            expected_source_path=SOURCE["VaultBook"],
            candidate_label=VAULT_BOOK_STAGED,
            registry_name="RipeHq",
            registry=hq,
            registry_id=8,
            expected_constructor_args=(
                hq,
                deployer,
                REGISTRY_MIN_DELAY,
                REGISTRY_MAX_DELAY,
            ),
        ),
        promotion("StabilityPool", "VaultBook", vault_book, 1, (hq,)),
        promotion("RipeGov", "VaultBook", vault_book, 2, (hq,)),
        promotion("AuctionHouse", "RipeHq", hq, 9, (hq,)),
        promotion("CreditEngine", "RipeHq", hq, 13, (hq, CURVE_PRICES_ID)),
        promotion(
            "HumanResources",
            "RipeHq",
            hq,
            15,
            (hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK),
        ),
        promotion(
            "Lootbox",
            "RipeHq",
            hq,
            16,
            (
                hq,
                LOOTBOX_MIN_SEND_INTERVAL,
                LOOTBOX_SEND_INTERVAL,
                LOOTBOX_DEPOSIT_REWARD,
                LOOTBOX_YIELD_BONUS,
            ),
        ),
        promotion(
            "Teller",
            "RipeHq",
            hq,
            17,
            (hq, TELLER_SHOULD_PAUSE, CURVE_PRICES_ID),
        ),
        promotion(
            "Deleverage",
            "RipeHq",
            hq,
            18,
            (hq, *deleverage_config(old_deleverage)),
        ),
        promotion("CreditRedeem", "RipeHq", hq, 19, (hq,)),
    )
    migration.promote_candidates(promotions)


def as_address(value):
    return str(getattr(value, "address", value)).lower()


def require_slot(registry, reg_id, expected):
    assert as_address(registry.getAddr(reg_id)) == as_address(expected)


def promotion(name, registry_name, registry, reg_id, constructor_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=SOURCE[name],
        candidate_label=staged(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=reg_id,
        expected_constructor_args=constructor_args,
    )


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def require_chainlink_copy(old, fresh):
    old_assets = tuple(old.getPricedAssets())
    fresh_assets = tuple(fresh.getPricedAssets())
    assert tuple(map(as_address, fresh_assets)) == tuple(map(as_address, old_assets))
    for asset in old_assets:
        assert normalized(fresh.feedConfig(asset)) == normalized(old.feedConfig(asset))


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
