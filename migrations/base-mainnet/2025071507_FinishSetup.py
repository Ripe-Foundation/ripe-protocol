from scripts.utils.migration import Migration


def migrate(migration: Migration):
    sb_alpha = migration.get_contract("SwitchboardAlpha")
    sb_bravo = migration.get_contract("SwitchboardBravo")
    sb_charlie = migration.get_contract("SwitchboardCharlie")
    sb_delta = migration.get_contract("SwitchboardDelta")

    chainlink = migration.get_contract("ChainlinkPrices")
    curve_prices = migration.get_contract("CurvePrices")
    bluechip_yield_prices = migration.get_contract("BlueChipYieldPrices")
    pyth_prices = migration.get_contract("PythPrices")
    stork_prices = migration.get_contract("StorkPrices")

    switchboard = migration.get_contract("Switchboard")
    price_desk = migration.get_contract("PriceDesk")
    vault_book = migration.get_contract("VaultBook")

    # Set time locks after setup
    migration.execute(sb_alpha.setActionTimeLockAfterSetup)
    migration.execute(sb_bravo.setActionTimeLockAfterSetup)
    migration.execute(sb_charlie.setActionTimeLockAfterSetup)
    migration.execute(sb_delta.setActionTimeLockAfterSetup)

    migration.execute(chainlink.setActionTimeLockAfterSetup)
    migration.execute(curve_prices.setActionTimeLockAfterSetup)
    migration.execute(bluechip_yield_prices.setActionTimeLockAfterSetup)
    migration.execute(pyth_prices.setActionTimeLockAfterSetup)
    migration.execute(stork_prices.setActionTimeLockAfterSetup)

    # Set registry time lock after setup
    assert migration.execute(switchboard.setRegistryTimeLockAfterSetup)
    assert migration.execute(price_desk.setRegistryTimeLockAfterSetup)
    assert migration.execute(vault_book.setRegistryTimeLockAfterSetup)

    migration.execute(sb_alpha.relinquishGov)
    migration.execute(sb_bravo.relinquishGov)
    migration.execute(sb_charlie.relinquishGov)
    migration.execute(sb_delta.relinquishGov)

    migration.execute(chainlink.relinquishGov)
    migration.execute(curve_prices.relinquishGov)
    migration.execute(bluechip_yield_prices.relinquishGov)
    migration.execute(pyth_prices.relinquishGov)
    migration.execute(stork_prices.relinquishGov)

    migration.execute(switchboard.relinquishGov)
    migration.execute(price_desk.relinquishGov)
    migration.execute(vault_book.relinquishGov)
