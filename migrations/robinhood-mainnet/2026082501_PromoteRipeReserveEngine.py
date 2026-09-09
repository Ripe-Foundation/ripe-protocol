"""Verify the activated RH Reserve Engine generation and promote its records.

This migration sends no transactions.  It checks every live registry and
activation value before replacing the four canonical manifest records.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)


CANDIDATE_SUFFIX = "Candidate2026082500"

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"

ENGINE_CONFIG = (
    10_000_000,
    100_000,
    8_000_000_000_000_000_000,
    4_000_000_000_000_000_000,
    6_000,
    4_000,
    1_000,
    3_000,
    300,
    800,
    800,
    4,
    1_000,
    100,
    600,
    300,
)
ALLOCATION_BUDGET = 1_000 * 10**18

SOURCE = {
    "VaultMigrator": "contracts/core/VaultMigrator.vy",
    "RipeReserveEngine": "contracts/core/RipeReserveEngine.vy",
    "RipeReserveVesting": "contracts/core/RipeReserveVesting.vy",
    "SwitchboardFoxtrot": "contracts/config/SwitchboardFoxtrot.vy",
}


def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    # ---------------------------------------------------------------------
    # 1. Read the exact candidates deployed by 2026082500.
    # ---------------------------------------------------------------------
    log.h1("1. Reading the Reserve Engine candidates")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    vault_migrator = migration.get_contract(candidate("VaultMigrator"))
    engine = migration.get_contract(candidate("RipeReserveEngine"))
    vesting = migration.get_contract(candidate("RipeReserveVesting"))
    foxtrot = migration.get_contract(candidate("SwitchboardFoxtrot"))

    # ---------------------------------------------------------------------
    # 2. Verify the complete live activation.
    # ---------------------------------------------------------------------
    log.h1("2. Checking registry and activation readbacks")

    assert address(hq.getAddr(25)) == address(vault_migrator)
    assert address(hq.getAddr(26)) == address(engine)
    assert address(hq.getAddr(27)) == address(vesting)
    assert address(switchboard.getAddr(6)) == address(foxtrot)
    assert int(hq.numAddrs()) == 28
    assert int(switchboard.numAddrs()) == 7

    assert bool(vault_migrator.isPaused())
    assert not bool(engine.isPaused())
    assert not bool(vesting.isPaused())
    assert bool(engine.isRunning())
    assert bool(engine.canAcquireRipe())
    assert bool(hq.canMintRipe(engine))
    assert not bool(hq.canMintRipe(vesting))
    assert address(engine.paymentToken()) == address(USDG)
    assert int(engine.paymentScale()) == 10**6
    assert tuple(map(int, engine.engineConfig())) == ENGINE_CONFIG
    assert int(vesting.remainingAllocationBudget()) == ALLOCATION_BUDGET
    assert int(foxtrot.actionTimeLock()) == 0
    assert address(foxtrot.governance()) == ZERO_ADDRESS

    # ---------------------------------------------------------------------
    # 3. Authenticate constructor inputs and promote all four records.
    # ---------------------------------------------------------------------
    log.h1("3. Promoting the Reserve Engine deployment records")

    migration.promote_candidates(
        (
            promotion(
                "VaultMigrator",
                "RipeHq",
                hq,
                25,
                (hq, True, ZERO_ADDRESS),
            ),
            promotion(
                "RipeReserveEngine",
                "RipeHq",
                hq,
                26,
                (hq, USDG, ENGINE_CONFIG),
            ),
            promotion(
                "RipeReserveVesting",
                "RipeHq",
                hq,
                27,
                (hq,),
            ),
            promotion(
                "SwitchboardFoxtrot",
                "Switchboard",
                switchboard,
                6,
                (
                    hq,
                    migration.account(),
                    SWITCHBOARD_MIN_TIMELOCK,
                    SWITCHBOARD_MAX_TIMELOCK,
                ),
            ),
        )
    )


def address(value):
    return str(getattr(value, "address", value)).lower()


def promotion(name, registry_name, registry, reg_id, constructor_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=SOURCE[name],
        candidate_label=candidate(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=reg_id,
        expected_constructor_args=constructor_args,
    )
