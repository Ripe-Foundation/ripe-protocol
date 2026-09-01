"""Print the Safe transaction that parks and snapshots PR #211 reward state.

This migration deploys nothing and changes nothing itself.  It reads the live
boards and Ledger, prints cancellation calls only for actions that are still
pending, and discovers every initialized deposit-points row instead of relying
on a stale handwritten asset list.

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
LOOTBOX = "0xc9fD8dFE6a9A0dB2dE53cC56b8E3b2892F33979a"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"

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
    lootbox = migration.get_contract("Lootbox", LOOTBOX)
    teller = migration.get_contract("Teller", TELLER)

    require_slot(hq, 4, ledger)
    require_slot(hq, 5, mission_control)
    require_slot(hq, 8, vault_book)
    require_slot(hq, 16, lootbox)
    require_slot(hq, 17, teller)

    boards = {
        name: migration.get_contract(contract_name(name), board_address)
        for name, board_address in BOARD_ADDRESSES.items()
    }
    for registry_id, name in ((1, "alpha"), (2, "bravo"), (3, "charlie"), (4, "delta"), (6, "foxtrot")):
        require_slot(switchboard, registry_id, boards[name])
        assert int(boards[name].actionTimeLock()) == 0

    rows = initialized_rows(mission_control, ledger, vault_book)
    current_rate = int(mission_control.rewardsConfig()[1])
    if current_rate == 0:
        raise RuntimeError("PR211_REWARD_RATE_ALREADY_ZERO")
    if bool(teller.isPaused()):
        raise RuntimeError("PR211_TELLER_ALREADY_PAUSED")
    if bool(lootbox.isPaused()):
        raise RuntimeError("PR211_LOOTBOX_MUST_REMAIN_UNPAUSED")

    log.h1("2. Safe park, checkpoint, and emission stop")
    print_safe_batch(boards, rows, current_rate)


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


def print_safe_batch(boards, rows, current_rate):
    for name in ("charlie", "foxtrot", "bravo", "alpha", "delta"):
        log.info(
            f'const {name} = c.Ripe_RH_{contract_name(name)}.at('
            f'"{BOARD_ADDRESSES[name]}")'
        )
    log.info("const zeroRateActionId = await alpha.actionId()")
    log.info("")

    pending_count = 0
    log.info("// 1. Cancel only actions that are pending at generation time")
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

    log.info("// 2. Park Teller while the old Lootbox remains unpaused")
    log.info(f'await charlie.pause("{TELLER}", true)')
    log.info("")

    log.info("// 3. Stamp the global reward bucket and every initialized row")
    log.info("await charlie.updateRipeRewards()")
    for asset, vault_id, vault, last_update in rows:
        name = ASSET_NAMES.get(asset.lower(), asset)
        log.info(
            f'await charlie.checkpointAssetDepositPointsAt("{asset}", '
            f'{vault_id}n, "{vault}")  // {name}; previous {last_update}'
        )
    log.info("")

    log.info("// 4. Set emissions to zero after all rows are stamped")
    log.info(f"// Record this live rate for restart: {current_rate}")
    log.info("await alpha.setRipePerBlock(0n)")
    log.info("await alpha.executePendingAction(zeroRateActionId)")
    log.info("")
    log.info("// Wait for a finalized archive-served block, regenerate Defaults,")
    log.info("// run verify_defaults.py, then run migration 2026082900.")


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
