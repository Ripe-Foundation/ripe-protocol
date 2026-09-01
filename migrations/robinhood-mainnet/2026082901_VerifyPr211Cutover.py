"""Verify the parked PR #211 cutover and print the step-8 restart batch.

This migration is read-only. Run it after the parked Safe cutover. It refuses
to print restart calls unless every replacement slot, retained root, reward
setting, and parked protocol path has the intended intermediate value.
"""

from config.robinhood_launch import ZERO_ADDRESS
from scripts.utils import log
from scripts.utils.migration import Migration


STAGED_SUFFIX = "Cutover2026082900"

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
LEDGER = "0x7E1d751D168f09761b88651A4c78C996354FaeB1"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"
HUMAN_RESOURCES = "0xfe4BAbbD48D31228872a7010E792244E66A22952"
RIPE_RESERVE_ENGINE = "0xc60af65F0bF8a1456aD822e98c45769552B13190"
RIPE_RESERVE_VESTING = "0x92ea6b99F1a0Cf95863DBf5CD83B0a09449ad396"
SWITCHBOARD_DELTA = "0x5F96d6090A5C88bd863051bb953F15163aD9e95a"

RESTORE_RIPE_PER_BLOCK = 41_666_666_666_666_666


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    log.h1("1. Reading the activated PR #211 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    ledger = migration.get_contract("Ledger", LEDGER)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    teller = migration.get_contract("Teller", TELLER)
    human_resources = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    reserve_engine = migration.get_contract("RipeReserveEngine", RIPE_RESERVE_ENGINE)
    reserve_vesting = migration.get_contract("RipeReserveVesting", RIPE_RESERVE_VESTING)

    mission_control = migration.get_contract(staged("MissionControl"))
    lootbox = migration.get_contract(staged("Lootbox"))
    alpha = migration.get_contract(staged("SwitchboardAlpha"))
    bravo = migration.get_contract(staged("SwitchboardBravo"))
    charlie = migration.get_contract(staged("SwitchboardCharlie"))
    foxtrot = migration.get_contract(staged("SwitchboardFoxtrot"))
    auction_house = migration.get_contract(staged("AuctionHouse"))
    deleverage = migration.get_contract(staged("Deleverage"))
    credit_redeem = migration.get_contract(staged("CreditRedeem"))

    log.h1("2. Checking registry and parked-state readbacks")

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

    if not bool(teller.isPaused()):
        raise RuntimeError("PR211_TELLER_REOPENED_BEFORE_READBACK")
    if bool(reserve_engine.canAcquireRipe()):
        raise RuntimeError("PR211_RESERVE_ACQUIRE_REOPENED_BEFORE_READBACK")
    if not bool(reserve_engine.isRunning()):
        raise RuntimeError("PR211_RESERVE_ENGINE_STOPPED")
    if not bool(reserve_vesting.isPaused()):
        raise RuntimeError("PR211_RESERVE_VESTING_REOPENED_BEFORE_READBACK")
    if bool(lootbox.isPaused()):
        raise RuntimeError("PR211_NEW_LOOTBOX_UNEXPECTEDLY_PAUSED")

    rewards = mission_control.rewardsConfig()
    assert int(rewards[1]) == 0
    assert int(rewards[5]) == 0
    assert int(mission_control.numAssets()) == 14
    assert tuple(map(int, mission_control.totalPointsAllocs())) == (9_000, 0)
    require_reward_vaults(mission_control)

    log.h1("3. Step 8 — restore emissions and reopen the protocol")
    print_restart(alpha, charlie, foxtrot)


def print_restart(alpha, charlie, foxtrot):
    log.info(f'const newAlpha = c.Ripe_RH_SwitchboardAlpha.at("{alpha.address}")')
    log.info(f'const newCharlie = c.Ripe_RH_SwitchboardCharlie.at("{charlie.address}")')
    log.info(f'const newFoxtrot = c.Ripe_RH_SwitchboardFoxtrot.at("{foxtrot.address}")')
    log.info("const restoreActionId = await newAlpha.actionId()")
    log.info("")
    log.info(f"await newAlpha.setRipePerBlock({RESTORE_RIPE_PER_BLOCK}n)")
    log.info("await newAlpha.executePendingAction(restoreActionId)")
    log.info(f'await newCharlie.pause("{TELLER}", false)')
    log.info(f'await newCharlie.pause("{RIPE_RESERVE_VESTING}", false)')
    log.info("await newFoxtrot.setCanAcquireRipe(true)")
    log.info("")
    log.info("// Execute this as a separate Safe batch, then run 2026082902.")


def require_reward_vaults(mission_control):
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        vault_ids = tuple(map(int, mission_control.assetConfig(asset)[0]))
        expected = vault_ids[0] if len(vault_ids) == 1 else 0
        assert int(mission_control.rewardVaultId(asset)) == expected


def require_slot(registry, registry_id, expected):
    if address(registry.getAddr(registry_id)) != address(expected):
        raise RuntimeError(f"PR211_VERIFY_SLOT_MISMATCH:{registry_id}")


def address(value):
    return str(getattr(value, "address", value)).lower()
