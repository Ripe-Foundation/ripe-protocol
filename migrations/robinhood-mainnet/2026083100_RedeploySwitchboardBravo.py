"""Deploy the voter-reweight SwitchboardBravo and print its Safe activation."""

import boa

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration


CANDIDATE_LABEL = "SwitchboardBravoVoterReweightCandidate2026083100"
SWITCHBOARD_BRAVO_ID = 2
ACTIVE_BRAVO = "0xB3223c7ecf1E2055add089F2cc0b88A4d9Fe4b75"


def migrate(migration: Migration):
    log.h1("1. Checking the active SwitchboardBravo")

    hq = migration.get_contract("RipeHq")
    switchboard = migration.get_contract("Switchboard")
    active_bravo = migration.get_contract("SwitchboardBravo")

    assert address(active_bravo) == address(ACTIVE_BRAVO)
    assert address(switchboard.getAddr(SWITCHBOARD_BRAVO_ID)) == address(
        active_bravo
    )
    assert int(switchboard.registryChangeTimeLock()) == 0

    log.h1("2. Deploying the voter-reweight candidate")

    candidate = migration.deploy(
        "SwitchboardBravo",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=CANDIDATE_LABEL,
    )
    assert address(candidate.governance()) in (
        address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        candidate.relinquishGov,
        lambda: address(candidate.governance()) == ZERO_ADDRESS,
    )
    assert address(candidate.governance()) == ZERO_ADDRESS
    assert int(candidate.actionTimeLock()) == 0
    assert int(candidate.actionId()) == 0
    if len(boa.env.get_code(candidate.address)) > 24_576:
        raise RuntimeError("SWITCHBOARD_BRAVO_RUNTIME_TOO_LARGE")

    log.h1("3. Safe activation")
    log.info(
        f'const switchboard = c.Ripe_RH_Switchboard.at("{switchboard.address}")'
    )
    log.info(
        "await switchboard.startAddressUpdateToRegistry("
        f'{SWITCHBOARD_BRAVO_ID}n, "{candidate.address}")'
    )
    log.info(
        "await switchboard.confirmAddressUpdateToRegistry("
        f"{SWITCHBOARD_BRAVO_ID}n)"
    )
    log.info("")
    log.info("After Safe execution, run migration 2026083101.")


def address(value):
    return str(getattr(value, "address", value)).lower()
