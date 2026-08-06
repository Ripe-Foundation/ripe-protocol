from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import (
    LOCAL_GOV_MAX_TIMELOCK,
    LOCAL_GOV_MIN_TIMELOCK,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
)


# The switchboards, in the exact order they take Switchboard registry ids 1-5.
BOARDS = ("Alpha", "Bravo", "Charlie", "Delta", "Echo")


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Switchboard")

    # Every department is constructed with ZERO local governance, not the
    # deployer: LocalGov asserts `_initialGov != hqGov`, and the deployer IS
    # RipeHq governance until the handoff. Passing the deployer here reverts.
    switchboard = migration.deploy(
        "Switchboard",
        hq,
        ZERO_ADDRESS,
        LOCAL_GOV_MIN_TIMELOCK,
        LOCAL_GOV_MAX_TIMELOCK,
    )

    for index, name in enumerate(BOARDS, start=1):
        log.h2(f"Deploying Switchboard{name}")
        args = [hq, ZERO_ADDRESS]
        if name == "Alpha":
            # Alpha alone takes the stale-window band before its timelocks.
            args += [
                STALE_WINDOW_MIN,
                STALE_WINDOW_MAX,
            ]
        args += [
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ]
        board = migration.deploy(f"Switchboard{name}", *args)

        migration.execute(
            switchboard.startAddNewAddressToRegistry, board, f"Switchboard{name}"
        )
        assert int(
            migration.execute(switchboard.confirmNewAddressToRegistry, board)
        ) == index

    # Switchboard itself takes RipeHq id 6, after its five members are in place.
    migration.execute(hq.startAddNewAddressToRegistry, switchboard, "Switchboard")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, switchboard)) == 6
