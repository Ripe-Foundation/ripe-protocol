from scripts.utils.migration import Migration


OLD_ENDAOMENT =  "0xd00A4A131b26920b6f407D177bCCa94454EAEF7d"

def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    new_endaoment = migration.deploy(
        "Endaoment",
        hq,
        migration.blueprint().ADDYS["WETH"],
        migration.blueprint().ADDYS["ETH"],
    )

    # switchboard charlie
    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        migration.account(),
        3_600,  # 2 hours
        migration.blueprint().PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    
    migration.execute(
        switchboard_charlie.addPartnerLiquidityInEndaoment, 
        10,
        migration.get_address("GreenPool"),
        OLD_ENDAOMENT,
        migration.blueprint().CORE_TOKENS["USDC"],
    )
    migration.execute(
        switchboard_charlie.recoverFundsMany,
        OLD_ENDAOMENT,
        new_endaoment,
        [
            migration.get_address("RipeToken"),
            migration.get_address("RipePoolAero"),
            migration.get_address("GreenPool"),
        ],
    )

    migration.execute(switchboard_charlie.setActionTimeLockAfterSetup)
    migration.execute(switchboard_charlie.relinquishGov)


    bond_booster = migration.deploy(
        "BondBooster",
        hq,
        200_00,  # _maxBoostRatio
        25_000,  # _maxUnits
        43_200 * 30 * 6,  # _minLockDuration - 6 months
    )

    migration.deploy(
        "BondRoom",
        hq,
        bond_booster,
    )

    # switchboard delta
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        3_600,  # 2 hours
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.relinquishGov)

    
