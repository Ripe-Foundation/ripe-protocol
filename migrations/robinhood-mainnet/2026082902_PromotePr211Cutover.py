"""Verify the reopened PR #211 generation and publish canonical manifest names.

This migration sends no transaction. It fails unless every reviewed registry
replacement is live, every retained root is unchanged, all parked paths were
reopened, and emissions were restored. Promotion removes the temporary
cutover and confirmation-helper labels from ``current-manifest.json``.
"""

from config.robinhood_launch import (
    PYTH_PRICES_ID,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec


STAGED_SUFFIX = "Cutover2026082900"
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
LEDGER = "0x7E1d751D168f09761b88651A4c78C996354FaeB1"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"
HUMAN_RESOURCES = "0xfe4BAbbD48D31228872a7010E792244e66A22952"
RIPE_RESERVE_ENGINE = "0xc60af65F0bF8a1456aD822e98c45769552B13190"
RIPE_RESERVE_VESTING = "0x92ea6b99F1a0Cf95863DBf5CD83B0a09449ad396"
SWITCHBOARD_DELTA = "0x5F96d6090A5C88bd863051bb953F15163aD9e95a"
CONTRIBUTOR = "0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68"

RESTORE_RIPE_PER_BLOCK = 41_666_666_666_666_666
LOOTBOX_ARGS = (1, 0, 0, 0)
DELEVERAGE_ARGS = (0, 0, 0, 100, 10**15, 100, 0, 0)

SOURCE = {
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
    "MissionControl": "contracts/data/MissionControl.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "SwitchboardAlpha": "contracts/config/SwitchboardAlpha.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "SwitchboardFoxtrot": "contracts/config/SwitchboardFoxtrot.vy",
    "AuctionHouse": "contracts/core/AuctionHouse.vy",
    "Deleverage": "contracts/core/Deleverage.vy",
    "CreditRedeem": "contracts/core/CreditRedeem.vy",
}


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    log.h1("1. Reading the reopened PR #211 cutover")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    ledger = migration.get_contract("Ledger", LEDGER)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    teller = migration.get_contract("Teller", TELLER)
    human_resources = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    reserve_engine = migration.get_contract("RipeReserveEngine", RIPE_RESERVE_ENGINE)
    reserve_vesting = migration.get_contract("RipeReserveVesting", RIPE_RESERVE_VESTING)
    contributor = migration.get_contract("Contributor", CONTRIBUTOR)

    defaults = migration.get_contract(staged("DefaultsRobinhoodLive"))
    mission_control = migration.get_contract(staged("MissionControl"))
    lootbox = migration.get_contract(staged("Lootbox"))
    alpha = migration.get_contract(staged("SwitchboardAlpha"))
    bravo = migration.get_contract(staged("SwitchboardBravo"))
    charlie = migration.get_contract(staged("SwitchboardCharlie"))
    foxtrot = migration.get_contract(staged("SwitchboardFoxtrot"))
    auction_house = migration.get_contract(staged("AuctionHouse"))
    deleverage = migration.get_contract(staged("Deleverage"))
    credit_redeem = migration.get_contract(staged("CreditRedeem"))
    log.h1("2. Checking final registry and reopened-state readbacks")

    for registry_id, contract in (
        (4, ledger),
        (5, mission_control),
        (8, vault_book),
        (9, auction_house),
        (15, human_resources),
        (16, lootbox),
        (17, teller),
        (18, deleverage),
        (19, credit_redeem),
        (26, reserve_engine),
        (27, reserve_vesting),
    ):
        require_slot(hq, registry_id, contract)

    for registry_id, contract in (
        (1, alpha),
        (2, bravo),
        (3, charlie),
        (4, SWITCHBOARD_DELTA),
        (6, foxtrot),
    ):
        require_slot(switchboard, registry_id, contract)

    for board in (alpha, bravo, charlie, foxtrot):
        assert address(board.governance()) == ZERO_ADDRESS
        assert int(board.actionTimeLock()) == 0

    if bool(teller.isPaused()):
        raise RuntimeError("PR211_TELLER_NOT_REOPENED")
    if not bool(reserve_engine.canAcquireRipe()):
        raise RuntimeError("PR211_RESERVE_ACQUIRE_NOT_REOPENED")
    if not bool(reserve_engine.isRunning()):
        raise RuntimeError("PR211_RESERVE_ENGINE_STOPPED")
    if bool(reserve_vesting.isPaused()):
        raise RuntimeError("PR211_RESERVE_VESTING_NOT_REOPENED")
    if bool(lootbox.isPaused()):
        raise RuntimeError("PR211_NEW_LOOTBOX_NOT_REOPENED")

    rewards = mission_control.rewardsConfig()
    assert int(rewards[1]) == RESTORE_RIPE_PER_BLOCK
    assert int(rewards[5]) == 0
    assert int(mission_control.numAssets()) == 14
    assert tuple(map(int, mission_control.totalPointsAllocs())) == (9_000, 0)
    require_reward_vaults(mission_control)
    log.h1("3. Publishing canonical PR #211 manifest records")

    deployer = migration.account()
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
        promotion("MissionControl", "RipeHq", hq, 5, (hq, defaults)),
        promotion("Lootbox", "RipeHq", hq, 16, (hq, *LOOTBOX_ARGS)),
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
            "SwitchboardFoxtrot",
            "Switchboard",
            switchboard,
            6,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion("AuctionHouse", "RipeHq", hq, 9, (hq,)),
        promotion("Deleverage", "RipeHq", hq, 18, (hq, *DELEVERAGE_ARGS)),
        promotion("CreditRedeem", "RipeHq", hq, 19, (hq,)),
    )
    migration.promote_candidates(promotions)


def promotion(name, registry_name, registry, registry_id, constructor_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=SOURCE[name],
        candidate_label=staged(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=registry_id,
        expected_constructor_args=constructor_args,
    )


def require_reward_vaults(mission_control):
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        vault_ids = tuple(map(int, mission_control.assetConfig(asset)[0]))
        expected = vault_ids[0] if len(vault_ids) == 1 else 0
        assert int(mission_control.rewardVaultId(asset)) == expected


def require_slot(registry, registry_id, expected):
    if address(registry.getAddr(registry_id)) != address(expected):
        raise RuntimeError(f"PR211_PROMOTION_SLOT_MISMATCH:{registry_id}")


def address(value):
    return str(getattr(value, "address", value)).lower()
