"""Print the updated Safe transaction that parks PR #211 reward state.

This migration is read-only. It inspects the current live state and prints only
the calls still needed to park deposits, Reserve Engine acquisition/claims,
checkpoint rewards, stop emissions, and finally pause Lootbox.

Execute the printed Safe transaction, wait for a finalized archive-served
block, regenerate ``DefaultsRobinhoodLive.vy``, and only then run 2026082900.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
LEDGER = "0x7E1d751D168f09761b88651A4c78C996354FaeB1"
MISSION_CONTROL = "0xC154F6fCA0788947E49Ffb4AD121F03C8332EFDe"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
HUMAN_RESOURCES = "0xfe4BAbbD48D31228872A7010E792244E66A22952"
LOOTBOX = "0xc9fD8dFE6a9A0dB2dE53cC56b8E3b2892F33979a"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"
RIPE_RESERVE_ENGINE = "0xc60af65F0bF8a1456aD822e98c45769552B13190"
RIPE_RESERVE_VESTING = "0x92ea6b99F1a0Cf95863DBf5CD83B0a09449ad396"

BOARD_ADDRESSES = {
    "alpha": "0xc36b4E857A6430e0D848eaA3C664B855F804Cc26",
    "bravo": "0xd7F1d8BBB1f06879fBbdda695d35C5aa0117394f",
    "charlie": "0xc4d4E0EBC6b40FC31893449327E7080feE2CEA20",
    "delta": "0x5F96d6090A5C88bd863051bb953F15163aD9e95a",
    "foxtrot": "0xD11B23b6391e294DF49961E64231bddDE5bB5E89",
}

ASSET_NAMES = {
    "0x0bd7d308f8e1639fab988df18a8011f41eacad73": "WETH",
    "0x4a0e65a3eccec6dbe60ae065f2e7bb85fae35eea": "SPCX",
    "0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec": "NVDA",
    "0x322f0929c4625ed5bad873c95208d54e1c003b2d": "TSLA",
    "0xaf3d76f1834a1d425780943c99ea8a608f8a93f9": "AAPL",
    "0x2e0847e8910a9732eb3fb1bb4b70a580adad4fe3": "GOOGL",
    "0x1b0e319c6a659f002271b69db8a7df2f911c153e": "GME",
    "0x4d3f37a965b21ab4122e92dd41d2693e742c883b": "RIPE",
    "0xba6f6cba1a4104000847d4fdccb676e99166cece": "RIPE/WETH LP",
    "0x9b8537be0fd5cf9b2ad495c5a85130d5bae4769d": "RIPE/NVDA LP",
    "0x290a52380a88f743813b8c3e9f6b0e61db5fdf73": "sGREEN",
    "0x2fd13b49f970e8c6d89283056c1c6281214b7eb6": "GREEN/USDG LP",
    "0x355bb7f0f6c730e4460d620420a300fa08ff82f3": "GREEN",
}


def migrate(migration: Migration):
    log.h1("1. Reading the live PR #211 park state")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    ledger = migration.get_contract("Ledger", LEDGER)
    mission_control = migration.get_contract("MissionControl", MISSION_CONTROL)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    human_resources = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    lootbox = migration.get_contract("Lootbox", LOOTBOX)
    teller = migration.get_contract("Teller", TELLER)
    engine = migration.get_contract("RipeReserveEngine", RIPE_RESERVE_ENGINE)
    vesting = migration.get_contract("RipeReserveVesting", RIPE_RESERVE_VESTING)

    for registry_id, contract in (
        (4, ledger),
        (5, mission_control),
        (8, vault_book),
        (15, human_resources),
        (16, lootbox),
        (17, teller),
        (26, engine),
        (27, vesting),
    ):
        require_slot(hq, registry_id, contract)

    boards = {
        name: migration.get_contract(contract_name(name), board_address)
        for name, board_address in BOARD_ADDRESSES.items()
    }
    for registry_id, name in (
        (1, "alpha"),
        (2, "bravo"),
        (3, "charlie"),
        (4, "delta"),
        (6, "foxtrot"),
    ):
        require_slot(switchboard, registry_id, boards[name])
        assert int(boards[name].actionTimeLock()) == 0

    if not bool(engine.isRunning()):
        raise RuntimeError("PR211_RESERVE_ENGINE_NOT_RUNNING")
    if int(ledger.numContributors()) != 0:
        raise RuntimeError("PR211_LIVE_CONTRIBUTOR_REQUIRES_EXPLICIT_PARK")

    state = {
        "teller_paused": bool(teller.isPaused()),
        "can_acquire": bool(engine.canAcquireRipe()),
        "vesting_paused": bool(vesting.isPaused()),
        "lootbox_paused": bool(lootbox.isPaused()),
        "ripe_per_block": int(mission_control.rewardsConfig()[1]),
    }
    rows = initialized_rows(mission_control, ledger, vault_book)

    log.h1("2. Safe park, checkpoint, and emission stop")
    print_safe_batch(boards, rows, state)


def initialized_rows(mission_control, ledger, vault_book):
    rows = []
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        for vault_id in mission_control.assetConfig(asset)[0]:
            points = ledger.assetDepositPoints(vault_id, asset)
            if int(points.lastUpdate) == 0:
                continue
            rows.append(
                (
                    str(asset),
                    int(vault_id),
                    str(vault_book.getAddr(vault_id)),
                    int(points.lastUpdate),
                )
            )
    return tuple(rows)


def print_safe_batch(boards, rows, state):
    for name in ("alpha", "bravo", "charlie", "delta", "foxtrot"):
        log.info(
            f'const {name} = c.Ripe_RH_{contract_name(name)}.at('
            f'"{BOARD_ADDRESSES[name]}")'
        )
    log.info("")

    log.info("// 1. Cancel only actions still pending at generation time")
    pending_count = 0
    for name in ("charlie", "foxtrot", "bravo", "alpha", "delta"):
        board = boards[name]
        for action_id in range(1, int(board.actionId())):
            if not bool(board.hasPendingAction(action_id)):
                continue
            pending_count += 1
            log.info(f"await {name}.cancelPendingAction({action_id}n)")
    if pending_count == 0:
        log.info("// No pending board actions found")
    log.info("")

    log.info("// 2. Park every path that can write reward state")
    if state["teller_paused"]:
        log.info("// Teller is already paused")
    else:
        log.info(f'await charlie.pause("{TELLER}", true)')
    if state["can_acquire"]:
        log.info("await foxtrot.setCanAcquireRipe(false)")
    else:
        log.info("// Reserve Engine acquisition is already disabled")
    if state["vesting_paused"]:
        log.info("// Reserve vesting is already paused")
    else:
        log.info(f'await charlie.pause("{RIPE_RESERVE_VESTING}", true)')
    log.info("")

    current_rate = state["ripe_per_block"]
    if current_rate != 0:
        if state["lootbox_paused"]:
            raise RuntimeError("PR211_LOOTBOX_PAUSED_BEFORE_FINAL_CHECKPOINT")

        log.info("// 3. Stamp the global bucket and every initialized row")
        log.info("await charlie.updateRipeRewards()")
        for asset, vault_id, vault, last_update in rows:
            name = ASSET_NAMES.get(asset.lower(), asset)
            log.info(
                f'await charlie.checkpointAssetDepositPointsAt("{asset}", '
                f'{vault_id}n, "{vault}")  // {name}; previous {last_update}'
            )
        log.info("")

        log.info("// 4. Stop emissions after every row is stamped")
        log.info(f"// Record this live rate for restart: {current_rate}")
        log.info("const zeroRateActionId = await alpha.actionId()")
        log.info("await alpha.setRipePerBlock(0n)")
        log.info("await alpha.executePendingAction(zeroRateActionId)")
        log.info("")
    else:
        log.info("// 3-4. Emissions are already zero; do not stamp rows again")
        log.info("")

    log.info("// 5. Close direct Lootbox claims only after emissions are zero")
    if state["lootbox_paused"]:
        log.info("// Lootbox is already paused")
    else:
        log.info(f'await charlie.pause("{LOOTBOX}", true)')
    log.info("")
    log.info("// Read back: Teller paused, acquire disabled, engine still running,")
    log.info("// vesting paused, Lootbox paused, and ripePerBlock == 0.")
    log.info("// Then wait for a finalized archive-served block and regenerate Defaults.")


def contract_name(name):
    return {
        "alpha": "SwitchboardAlpha",
        "bravo": "SwitchboardBravo",
        "charlie": "SwitchboardCharlie",
        "delta": "SwitchboardDelta",
        "foxtrot": "SwitchboardFoxtrot",
    }[name]


def require_slot(registry, registry_id, expected):
    if address(registry.getAddr(registry_id)) != address(expected):
        raise RuntimeError(f"PR211_PREPARE_SLOT_MISMATCH:{registry_id}")


def address(value):
    return str(getattr(value, "address", value)).lower()
