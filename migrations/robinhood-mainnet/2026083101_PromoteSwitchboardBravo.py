"""Verify activation and publish the PR #211 Bravo canonically."""

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration


CANDIDATE_LABEL = "SwitchboardBravoPr211Candidate2026083100"
SWITCHBOARD_BRAVO_ID = 2
SOURCE_PATH = "contracts/config/SwitchboardBravo.vy"


def migrate(migration: Migration):
    log.h1("1. Verifying the activated SwitchboardBravo")

    hq = migration.get_contract("RipeHq")
    switchboard = migration.get_contract("Switchboard")
    candidate = migration.get_contract(CANDIDATE_LABEL)

    assert address(switchboard.getAddr(SWITCHBOARD_BRAVO_ID)) == address(
        candidate
    )
    assert address(candidate.governance()) == ZERO_ADDRESS
    assert int(candidate.actionTimeLock()) == 0

    log.h1("2. Publishing the canonical manifest record")
    migration.promote_candidate(
        "SwitchboardBravo",
        CANDIDATE_LABEL,
        switchboard,
        SWITCHBOARD_BRAVO_ID,
        expected_source_path=SOURCE_PATH,
        registry_name="Switchboard",
        expected_constructor_args=(
            hq,
            migration.account(),
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
    )


def address(value):
    return str(getattr(value, "address", value)).lower()
