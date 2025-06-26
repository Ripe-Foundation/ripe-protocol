from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    sb_alpha = migration.get_contract("SwitchboardAlpha")
    sb_bravo = migration.get_contract("SwitchboardBravo")
    sb_charlie = migration.get_contract("SwitchboardCharlie")
    sb_delta = migration.get_contract("SwitchboardDelta")
    chainlink = migration.get_contract("ChainlinkPrices")
    curve_prices = migration.get_contract("CurvePrices")
    human_resources = migration.get_contract("HumanResources")
    # bluechip_yield_prices = migration.get_contract("BlueChipYieldPrices")
    # pyth_prices = migration.get_contract("PythPrices")
    # stork_prices = migration.get_contract("StorkPrices")
    switchboard = migration.get_contract("Switchboard")
    price_desk = migration.get_contract("PriceDesk")
    vault_book = migration.get_contract("VaultBook")

    action_id = migration.execute(sb_alpha.setCanPerformLiteAction, '0x1c419AeF78b44F30D8F3Dfa2aB13D3538466dc48', True)
    assert bool(migration.execute(sb_alpha.executePendingAction, int(action_id)))
    action_id = migration.execute(sb_alpha.setCanPerformLiteAction, '0x6f5ef229d7F07183Bf91dF68702D01E9bDa37cA2', True)
    assert bool(migration.execute(sb_alpha.executePendingAction, int(action_id)))

    # Set time locks after setup
    migration.execute(sb_alpha.setActionTimeLockAfterSetup)
    migration.execute(sb_bravo.setActionTimeLockAfterSetup)
    migration.execute(sb_charlie.setActionTimeLockAfterSetup)
    migration.execute(sb_delta.setActionTimeLockAfterSetup)

    migration.execute(chainlink.setActionTimeLockAfterSetup)
    migration.execute(curve_prices.setActionTimeLockAfterSetup)
    # migration.execute(bluechip_yield_prices.setActionTimeLockAfterSetup)
    # migration.execute(pyth_prices.setActionTimeLockAfterSetup)
    # migration.execute(stork_prices.setActionTimeLockAfterSetup)

    migration.execute(human_resources.setActionTimeLockAfterSetup)

    # Set registry time lock after setup
    assert migration.execute(switchboard.setRegistryTimeLockAfterSetup)
    assert migration.execute(price_desk.setRegistryTimeLockAfterSetup)
    assert migration.execute(vault_book.setRegistryTimeLockAfterSetup)

    assert migration.execute(hq.setRegistryTimeLockAfterSetup)

    assert migration.execute(hq.finishRipeHqSetup, migration.blueprint().ADDYS["GOVERNANCE"])
