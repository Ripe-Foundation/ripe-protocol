from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


# Final, IRREVERSIBLE step. Everything below runs while the deployer still holds
# RipeHq governance; after finishRipeHqSetup the deployer has no authority left.
#
# Order matters: raise every action and registry time lock from its zero
# setup value FIRST, then hand over governance. Doing it the other way round
# would leave the protocol governed with zero-delay config actions.
def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    governance = blueprint.ADDYS["GOVERNANCE"]
    assert governance != ZERO_ADDRESS  # dev: governance identity unresolved
    assert governance != migration.account()  # dev: gov must not be the deployer

    sb_alpha = migration.get_contract("SwitchboardAlpha")
    sb_bravo = migration.get_contract("SwitchboardBravo")
    sb_charlie = migration.get_contract("SwitchboardCharlie")
    sb_delta = migration.get_contract("SwitchboardDelta")
    sb_echo = migration.get_contract("SwitchboardEcho")
    chainlink = migration.get_contract("ChainlinkPrices")
    bluechip_yield_prices = migration.get_contract("BlueChipYieldPrices")
    human_resources = migration.get_contract("HumanResources")
    switchboard = migration.get_contract("Switchboard")
    price_desk = migration.get_contract("PriceDesk")
    vault_book = migration.get_contract("VaultBook")

    log.h1("Setting action time locks after setup")

    migration.execute(sb_alpha.setActionTimeLockAfterSetup)
    migration.execute(sb_bravo.setActionTimeLockAfterSetup)
    migration.execute(sb_charlie.setActionTimeLockAfterSetup)
    migration.execute(sb_delta.setActionTimeLockAfterSetup)
    migration.execute(sb_echo.setActionTimeLockAfterSetup)

    migration.execute(chainlink.setActionTimeLockAfterSetup)
    migration.execute(bluechip_yield_prices.setActionTimeLockAfterSetup)

    migration.execute(human_resources.setActionTimeLockAfterSetup)

    log.h1("Setting registry time locks after setup")

    assert migration.execute(switchboard.setRegistryTimeLockAfterSetup)
    assert migration.execute(price_desk.setRegistryTimeLockAfterSetup)
    assert migration.execute(vault_book.setRegistryTimeLockAfterSetup)

    assert migration.execute(hq.setRegistryTimeLockAfterSetup)

    log.h1("Handing RipeHq governance to production governance")

    # NOTE: no relinquishGov calls are needed. Every department and registry was
    # deployed with ZERO_ADDRESS local gov, so RipeHq governance is the only
    # governor and this single handoff moves all of them at once.
    assert migration.execute(hq.finishRipeHqSetup, governance)
