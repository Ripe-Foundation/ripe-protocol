from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Endaoment")

    # The constructor now takes the native-asset sentinel as well as WETH, and
    # rejects a zero for either.
    endaoment = migration.deploy(
        "Endaoment",
        hq,
        blueprint.ADDYS["WETH"],
        blueprint.ADDYS["ETH"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, endaoment, "Endaoment")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, endaoment)) == 14

    # endaoment can mint green
    migration.execute(hq.initiateHqConfigChange, 14, True, False, False)
    migration.execute(hq.confirmHqConfigChange, 14)
