"""Verify the live PR #223 generation and publish canonical manifest names."""

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec


STAGED_SUFFIX = "Pr223Candidate2026082905"

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
CONTRIBUTOR = "0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68"
LOOTBOX_ARGS = (1, 0, 0, 0)

SOURCE = {
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
    "MissionControl": "contracts/data/MissionControl.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "SwitchboardFoxtrot": "contracts/config/SwitchboardFoxtrot.vy",
    "SwitchboardGolf": "contracts/config/SwitchboardGolf.vy",
}


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    log.h1("1. Verifying the activated PR #223 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    contributor = migration.get_contract("Contributor", CONTRIBUTOR)

    defaults = migration.get_contract(staged("DefaultsRobinhoodLive"))
    mission_control = migration.get_contract(staged("MissionControl"))
    lootbox = migration.get_contract(staged("Lootbox"))
    bravo = migration.get_contract(staged("SwitchboardBravo"))
    charlie = migration.get_contract(staged("SwitchboardCharlie"))
    foxtrot = migration.get_contract(staged("SwitchboardFoxtrot"))
    golf = migration.get_contract(staged("SwitchboardGolf"))

    require_slot(hq, 5, mission_control)
    require_slot(hq, 16, lootbox)
    require_slot(switchboard, 2, bravo)
    require_slot(switchboard, 3, charlie)
    require_slot(switchboard, 6, foxtrot)
    require_slot(switchboard, 7, golf)
    assert int(switchboard.getRegId(golf)) == 7

    for board in (bravo, charlie, foxtrot, golf):
        assert address(board.governance()) == ZERO_ADDRESS
        assert int(board.actionTimeLock()) == 0

    require_reward_vaults(mission_control)

    log.h1("2. Publishing canonical PR #223 manifest records")

    deployer = migration.account()
    board_args = (
        hq,
        deployer,
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
    )
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
        promotion("SwitchboardBravo", "Switchboard", switchboard, 2, board_args),
        promotion("SwitchboardCharlie", "Switchboard", switchboard, 3, board_args),
        promotion("SwitchboardFoxtrot", "Switchboard", switchboard, 6, board_args),
        promotion("SwitchboardGolf", "Switchboard", switchboard, 7, board_args),
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
        raise RuntimeError(f"PR223_PROMOTION_SLOT_MISMATCH:{registry_id}")


def address(value):
    return str(getattr(value, "address", value)).lower()
