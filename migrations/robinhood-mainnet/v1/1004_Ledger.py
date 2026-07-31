from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Ledger")

    # Robinhood is an Arbitrum L2: EVM `block.number` is the L1 ancestor estimate
    # and repeats across many child blocks, so the same-execution-block guard
    # cannot use it for action identity. The constructor takes the child-height
    # source explicitly (P-H04-309 approves ArbSys 0x64) and fail-closed probes
    # it at construction -- it accepts only zero (native) or exactly 0x64.
    ledger = migration.deploy(
        "Ledger",
        hq,
        migration.get_contract("DefaultsRobinHood"),
        blueprint.ADDYS["ARB_SYS"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, ledger)) == 4
