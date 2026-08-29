"""Deploy the reviewed PR #211 cutover generation without changing live pointers.

Run this only after the park/checkpoint/zero/snapshot steps in
``docs/chains/rh/pr-211-cutover-sequence.md``.  The preflight deliberately
rejects the checked-in stale Defaults file, a running reward clock, an
unpaused Teller, or any pending board action.

The migration deploys the ten contracts in the reviewed replace table plus a
temporary registry-readback helper, relinquishes temporary board governance,
and prints the ordered Safe cutover. Ledger, vaults, Teller, CreditEngine,
HumanResources, price sources, and both reserve contracts are retained.
"""

from pathlib import Path

import boa

from config.robinhood_launch import (
    PYTH_PRICES_ID,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration


STAGED_SUFFIX = "Cutover2026082900"
DEFAULTS_PATH = Path("contracts/config/DefaultsRobinhoodLive.vy")

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
LEDGER = "0x7E1d751D168f09761b88651A4c78C996354FaeB1"
MISSION_CONTROL = "0xC154F6fCA0788947E49Ffb4AD121F03C8332EFDe"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
AUCTION_HOUSE = "0x8241b4E94DBd10CEe02712b8b610142c6715E760"
LOOTBOX = "0xc9fD8dFE6a9A0dB2dE53cC56b8E3b2892F33979a"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"
HUMAN_RESOURCES = "0xfe4BAbbD48D31228872a7010E792244E66A22952"
RIPE_RESERVE_ENGINE = "0xc60af65F0bF8a1456aD822e98c45769552B13190"
RIPE_RESERVE_VESTING = "0x92ea6b99F1a0Cf95863DBf5CD83B0a09449ad396"
DELEVERAGE = "0xF98534c300036f7ccC6996eB6D63a5C538B53B2f"
CREDIT_REDEEM = "0x26b8733836aEeb3aa3B8Acee09dBa8E231299A87"
CONTRIBUTOR = "0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68"
SNAPSHOT_BLOCK = 48_799_076

SWITCHBOARD_ALPHA = "0xc36b4E857A6430e0D848eaA3C664B855F804Cc26"
SWITCHBOARD_BRAVO = "0xd7F1d8BBB1f06879fBbdda695d35C5aa0117394f"
SWITCHBOARD_CHARLIE = "0xc4d4E0EBC6b40FC31893449327E7080feE2CEA20"
SWITCHBOARD_DELTA = "0x5F96d6090A5C88bd863051bb953F15163aD9e95a"
SWITCHBOARD_FOXTROT = "0xD11B23b6391e294DF49961E64231bddDE5bB5E89"

LOOTBOX_ARGS = (1, 0, 0, 0)
DELEVERAGE_ARGS = (0, 0, 0, 100, 10**15, 100, 0, 0)


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Prove the live system is parked at the snapshot boundary.
    # ------------------------------------------------------------------
    log.h1("1. PR #211 cutover preflight")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    ledger = migration.get_contract("Ledger", LEDGER)
    old_mc = migration.get_contract("MissionControl", MISSION_CONTROL)
    old_lootbox = migration.get_contract("Lootbox", LOOTBOX)
    teller = migration.get_contract("Teller", TELLER)
    human_resources = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    reserve_engine = migration.get_contract("RipeReserveEngine", RIPE_RESERVE_ENGINE)
    reserve_vesting = migration.get_contract("RipeReserveVesting", RIPE_RESERVE_VESTING)
    contributor = migration.get_contract("Contributor", CONTRIBUTOR)

    require_slot(hq, 4, ledger)
    require_slot(hq, 5, old_mc)
    require_slot(hq, 8, VAULT_BOOK)
    require_slot(hq, 9, AUCTION_HOUSE)
    require_slot(hq, 15, human_resources)
    require_slot(hq, 16, old_lootbox)
    require_slot(hq, 17, teller)
    require_slot(hq, 18, DELEVERAGE)
    require_slot(hq, 19, CREDIT_REDEEM)
    require_slot(hq, 26, reserve_engine)
    require_slot(hq, 27, reserve_vesting)
    require_slot(switchboard, 1, SWITCHBOARD_ALPHA)
    require_slot(switchboard, 2, SWITCHBOARD_BRAVO)
    require_slot(switchboard, 3, SWITCHBOARD_CHARLIE)
    require_slot(switchboard, 4, SWITCHBOARD_DELTA)
    require_slot(switchboard, 6, SWITCHBOARD_FOXTROT)

    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0
    if not bool(teller.isPaused()):
        raise RuntimeError("PR211_TELLER_NOT_PARKED")
    if not bool(old_lootbox.isPaused()):
        raise RuntimeError("PR211_LOOTBOX_NOT_PARKED")
    if bool(reserve_engine.canAcquireRipe()):
        raise RuntimeError("PR211_RESERVE_ACQUIRE_NOT_PARKED")
    if not bool(reserve_engine.isRunning()):
        raise RuntimeError("PR211_RESERVE_ENGINE_STOPPED")
    if not bool(reserve_vesting.isPaused()):
        raise RuntimeError("PR211_RESERVE_VESTING_NOT_PARKED")
    if int(old_mc.rewardsConfig()[1]) != 0:
        raise RuntimeError("PR211_REWARD_RATE_NOT_ZERO")
    if int(ledger.numContributors()) != 0:
        raise RuntimeError("PR211_LIVE_CONTRIBUTOR_REQUIRES_EXPLICIT_PARK")
    assert int(old_mc.numAssets()) == 14  # one-indexed: 13 live assets
    assert tuple(map(int, old_mc.totalPointsAllocs())) == (9_000, 0)

    current_boards = (
        ("SwitchboardAlpha", migration.get_contract("SwitchboardAlpha", SWITCHBOARD_ALPHA)),
        ("SwitchboardBravo", migration.get_contract("SwitchboardBravo", SWITCHBOARD_BRAVO)),
        ("SwitchboardCharlie", migration.get_contract("SwitchboardCharlie", SWITCHBOARD_CHARLIE)),
        ("SwitchboardDelta", migration.get_contract("SwitchboardDelta", SWITCHBOARD_DELTA)),
        ("SwitchboardFoxtrot", migration.get_contract("SwitchboardFoxtrot", SWITCHBOARD_FOXTROT)),
    )
    for name, board in current_boards:
        assert int(board.actionTimeLock()) == 0
        require_no_pending_actions(name, board)

    require_fresh_defaults_snapshot()

    # ------------------------------------------------------------------
    # 2. Deploy only the reviewed replacement set.
    # ------------------------------------------------------------------
    log.h1("2. Deploying the PR #211 cutover generation")

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
    assert equivalent_mission_control(old_mc, mission_control)
    require_reward_vaults(mission_control)

    lootbox = migration.deploy(
        "Lootbox",
        hq,
        *LOOTBOX_ARGS,
        label=staged("Lootbox"),
    )
    auction_house = migration.deploy(
        "AuctionHouse", hq, label=staged("AuctionHouse")
    )
    credit_redeem = migration.deploy(
        "CreditRedeem", hq, label=staged("CreditRedeem")
    )
    deleverage = migration.deploy(
        "Deleverage",
        hq,
        *DELEVERAGE_ARGS,
        label=staged("Deleverage"),
    )

    alpha = deploy_board(
        migration,
        "SwitchboardAlpha",
        hq,
        migration.account(),
        STALE_WINDOW_MIN,
        STALE_WINDOW_MAX,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        PYTH_PRICES_ID,
    )
    bravo = deploy_board(
        migration,
        "SwitchboardBravo",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
    )
    charlie = deploy_board(
        migration,
        "SwitchboardCharlie",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
    )
    foxtrot = deploy_board(
        migration,
        "SwitchboardFoxtrot",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
    )
    # This view-only helper was deployed with the generation, but the Safe
    # script builder evaluates view calls before queued transactions. Leave it
    # unused; 2026082901 performs the authoritative post-cutover readback.
    migration.deploy(
        "ConfirmRegistryUpdate",
        label="ConfirmRegistryUpdateCandidate2026082900",
    )

    assert len(boa.env.get_code(auction_house.address)) <= 24_576
    assert len(boa.env.get_code(deleverage.address)) <= 24_576

    # ------------------------------------------------------------------
    # 3. Print the dependency-ordered Safe transaction.
    # ------------------------------------------------------------------
    log.h1("3. Parked Safe cutover")
    print_safe_batch(
        mission_control=mission_control,
        lootbox=lootbox,
        auction_house=auction_house,
        deleverage=deleverage,
        credit_redeem=credit_redeem,
        alpha=alpha,
        bravo=bravo,
        charlie=charlie,
        foxtrot=foxtrot,
    )


def deploy_board(migration, name, *args):
    board = migration.deploy(name, *args, label=staged(name))
    assert address(board.governance()) in (
        address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        board.relinquishGov,
        lambda: address(board.governance()) == ZERO_ADDRESS,
    )
    assert address(board.governance()) == ZERO_ADDRESS
    assert int(board.actionTimeLock()) == 0
    return board


def require_no_pending_actions(name, board):
    for action_id in range(1, int(board.actionId())):
        if bool(board.hasPendingAction(action_id)):
            raise RuntimeError(
                f"PR211_PENDING_ACTION:{name}:{action_id}"
            )


def require_fresh_defaults_snapshot():
    source = DEFAULTS_PATH.read_text()
    required = (
        f"#   snapshot block: {SNAPSHOT_BLOCK}",
        f"#   MissionControl: {MISSION_CONTROL}",
        f"#   Ledger: {LEDGER}",
        "ripePerBlock=0,",
    )
    missing = tuple(value for value in required if value not in source)
    if missing:
        raise RuntimeError("PR211_DEFAULTS_NOT_REGENERATED:" + ",".join(missing))


def equivalent_mission_control(old, fresh):
    getters = (
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
    if any(normalized(getattr(old, name)()) != normalized(getattr(fresh, name)()) for name in getters):
        return False

    old_assets = tuple(old.assets(i) for i in range(1, int(old.numAssets())))
    fresh_assets = tuple(fresh.assets(i) for i in range(1, int(fresh.numAssets())))
    if tuple(map(address, old_assets)) != tuple(map(address, fresh_assets)):
        return False
    for asset in old_assets:
        if normalized(old.assetConfig(asset)) != normalized(fresh.assetConfig(asset)):
            return False
        if normalized(old.ripeGovVaultConfig(asset)) != normalized(
            fresh.ripeGovVaultConfig(asset)
        ):
            return False

    old_signers = tuple(
        old.liteSigners(i) for i in range(1, int(old.numLiteSigners()))
    )
    fresh_signers = tuple(
        fresh.liteSigners(i) for i in range(1, int(fresh.numLiteSigners()))
    )
    if tuple(map(address, old_signers)) != tuple(map(address, fresh_signers)):
        return False

    for vault_id in range(1, 4):
        if bool(old.isStabVaultId(vault_id)) != bool(fresh.isStabVaultId(vault_id)):
            return False
        if bool(old.isRipeGovVaultId(vault_id)) != bool(
            fresh.isRipeGovVaultId(vault_id)
        ):
            return False
    return True


def require_reward_vaults(mission_control):
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        vault_ids = tuple(map(int, mission_control.assetConfig(asset)[0]))
        expected = vault_ids[0] if len(vault_ids) == 1 else 0
        assert int(mission_control.rewardVaultId(asset)) == expected


def require_slot(registry, registry_id, expected):
    if address(registry.getAddr(registry_id)) != address(expected):
        raise RuntimeError(f"PR211_ACTIVE_SLOT_MISMATCH:{registry_id}")


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def address(value):
    return str(getattr(value, "address", value)).lower()


def print_safe_batch(**fresh):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(f'const switchboard = c.Ripe_RH_Switchboard.at("{SWITCHBOARD}")')
    log.info(f'const newCharlie = c.Ripe_RH_SwitchboardCharlie.at("{fresh["charlie"].address}")')
    log.info("")
    log.info("// Confirm directly from governance; 2026082901 verifies every slot.")
    log.info("// Do not append the separate step-8 restart batch.")
    log.info("")

    log.info("// 1. Install Foxtrot before Charlie so auction control never disappears")
    print_registry_update("switchboard", 6, fresh["foxtrot"], "SwitchboardFoxtrot")
    print_registry_update("switchboard", 3, fresh["charlie"], "SwitchboardCharlie")
    log.info("")

    log.info("// 2. Install MissionControl before any board that uses rewardVaultId")
    print_registry_update("hq", 5, fresh["mission_control"], "MissionControl")
    print_registry_update("hq", 16, fresh["lootbox"], "Lootbox")
    log.info("await newCharlie.updateRipeRewards()")
    log.info("")

    log.info("// 3. Install the remaining boards and settlement contracts")
    print_registry_update("switchboard", 1, fresh["alpha"], "SwitchboardAlpha")
    print_registry_update("switchboard", 2, fresh["bravo"], "SwitchboardBravo")
    print_registry_update("hq", 9, fresh["auction_house"], "AuctionHouse")
    print_registry_update("hq", 18, fresh["deleverage"], "Deleverage")
    print_registry_update("hq", 19, fresh["credit_redeem"], "CreditRedeem")
    log.info("")

    log.info("// STOP. Execute this parked cutover, then run step 7 (2026082901).")


def print_registry_update(registry, registry_id, contract, name):
    log.info(
        f"await {registry}.startAddressUpdateToRegistry({registry_id}n, "
        f'"{contract.address}")  // {name}'
    )
    log.info(
        f"await {registry}.confirmAddressUpdateToRegistry({registry_id}n)  "
        f"// {name}"
    )
