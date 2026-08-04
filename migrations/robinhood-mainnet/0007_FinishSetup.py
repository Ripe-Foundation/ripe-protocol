from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import GOVERNANCE, address


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    # switchboard = migration.get_contract("Switchboard")
    # sb_alpha = migration.get_contract("SwitchboardAlpha")
    # sb_bravo = migration.get_contract("SwitchboardBravo")
    # sb_charlie = migration.get_contract("SwitchboardCharlie")
    # sb_delta = migration.get_contract("SwitchboardDelta")
    # sb_echo = migration.get_contract("SwitchboardEcho")
    # chainlink = migration.get_contract("ChainlinkPrices")
    # curve_prices = migration.get_contract("CurvePrices")
    # blue_chip = migration.get_contract("BlueChipYieldPrices")
    # human_resources = migration.get_contract("HumanResources")
    # price_desk = migration.get_contract("PriceDesk")
    # vault_book = migration.get_contract("VaultBook")

    # log.h1("Setting time locks after setup")

    # for board in (sb_alpha, sb_bravo, sb_charlie, sb_delta, sb_echo):
    #     migration.execute(board.setActionTimeLockAfterSetup)

    # migration.execute(chainlink.setActionTimeLockAfterSetup)
    # migration.execute(curve_prices.setActionTimeLockAfterSetup)
    # migration.execute(blue_chip.setActionTimeLockAfterSetup)
    # migration.execute(human_resources.setActionTimeLockAfterSetup)

    # assert migration.execute(switchboard.setRegistryTimeLockAfterSetup)
    # assert migration.execute(price_desk.setRegistryTimeLockAfterSetup)
    # assert migration.execute(vault_book.setRegistryTimeLockAfterSetup)
    # assert migration.execute(hq.setRegistryTimeLockAfterSetup)

    log.h1("Handing governance to the Safe")

    # Irreversible. After this the deployer governs nothing: the departments
    # were constructed holding zero local governance, so RipeHq is the only
    # authority that moves, and it moves once.
    assert migration.execute(hq.finishRipeHqSetup, GOVERNANCE)
