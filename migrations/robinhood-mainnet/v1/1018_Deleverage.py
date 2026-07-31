from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Deleverage")

    # P-H04-308 approves deleverageCooldown = 0 and the S4 decision is closed:
    # Robinhood keeps zero cooldown and omits Underscore, so the safe-spread
    # control is inert. The four corrected-PR controls (full payoff buffer,
    # overage, dust threshold, dust bps) are deferred at zero -- the contract
    # exposes them but no approved Robinhood value exists yet.
    #
    # minDeleverageBps and deleverageBuffer have NO approved Robinhood value and
    # currently mirror Base. Confirm both before a live run.
    deleverage = migration.deploy(
        "Deleverage",
        hq,
        blueprint.PARAMS["DELEVERAGE_MIN_BPS"],
        blueprint.PARAMS["DELEVERAGE_BUFFER"],
        blueprint.PARAMS["DELEVERAGE_COOLDOWN"],
        blueprint.PARAMS["DELEVERAGE_UNDERSCORE_SAFE_SPREAD_BPS"],
        blueprint.PARAMS["DELEVERAGE_FULL_PAYOFF_BUFFER"],
        blueprint.PARAMS["DELEVERAGE_OVERAGE_BPS"],
        blueprint.PARAMS["DELEVERAGE_DUST_THRESHOLD"],
        blueprint.PARAMS["DELEVERAGE_DUST_BPS"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, deleverage, "Deleverage")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, deleverage)) == 18

    # no mint capability needed
