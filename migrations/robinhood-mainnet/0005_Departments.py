from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    DELEVERAGE_BUFFER,
    DELEVERAGE_COOLDOWN,
    DELEVERAGE_DUST_BPS,
    DELEVERAGE_DUST_THRESHOLD,
    DELEVERAGE_FULL_PAYOFF_BUFFER,
    DELEVERAGE_MIN_BPS,
    DELEVERAGE_OVERAGE_BPS,
    DELEVERAGE_UNDERSCORE_SPREAD,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    address,
    approved,
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    def register(contract, name, expected_id):
        migration.execute(hq.startAddNewAddressToRegistry, contract, name)
        assert int(
            migration.execute(hq.confirmNewAddressToRegistry, contract)
        ) == expected_id

    log.h1("Deploying core departments")

    register(migration.deploy("AuctionHouse", hq), "AuctionHouse", 9)
    register(migration.deploy("AuctionHouseNFT", hq), "AuctionHouseNFT", 10)
    register(migration.deploy("Boardroom", hq), "Boardroom", 11)

    # BondBooster is a BondRoom constructor argument, so it is not registered.
    bond_booster = migration.deploy(
        "BondBooster",
        hq,
        approved("Deployment.DP-22.bondBooster.maxBoostRatio"),
        approved("Deployment.DP-22.bondBooster.maxUnits"),
        approved("Deployment.DP-22.bondBooster.minLockDuration"),
    )
    register(migration.deploy("BondRoom", hq, bond_booster), "BondRoom", 12)

    register(migration.deploy("CreditEngine", hq), "CreditEngine", 13)
    register(
        migration.deploy(
            "Endaoment",
            hq,
            approved("Deployment.DP-21.endaoment.wethIdentity"),
            address("NATIVE_ETH_SENTINEL"),
        ),
        "Endaoment",
        14,
    )
    register(
        migration.deploy(
            "HumanResources",
            hq,
            approved("Deployment.DP-05.timelocks.HumanResources.minTimeLock"),
            approved("Deployment.DP-05.timelocks.HumanResources.maxTimeLock"),
        ),
        "HumanResources",
        15,
    )

    # Every Lootbox parameter is an Underscore reward, and Underscore is absent
    # here. The send-interval floor must still be nonzero -- the constructor
    # asserts it is neither 0 nor max_value.
    register(
        migration.deploy(
            "Lootbox",
            hq,
            LOOTBOX_MIN_SEND_INTERVAL,
            LOOTBOX_SEND_INTERVAL,
            LOOTBOX_DEPOSIT_REWARD,
            LOOTBOX_YIELD_BONUS,
        ),
        "Lootbox",
        16,
    )

    # Teller launches paused.
    register(
        migration.deploy(
            "Teller", hq, approved("Deployment.DP-20.teller.shouldPause")
        ),
        "Teller",
        17,
    )

    register(
        migration.deploy(
            "Deleverage",
            hq,
            DELEVERAGE_MIN_BPS,
            DELEVERAGE_BUFFER,
            DELEVERAGE_COOLDOWN,
            DELEVERAGE_UNDERSCORE_SPREAD,
            DELEVERAGE_FULL_PAYOFF_BUFFER,
            DELEVERAGE_OVERAGE_BPS,
            DELEVERAGE_DUST_THRESHOLD,
            DELEVERAGE_DUST_BPS,
        ),
        "Deleverage",
        18,
    )

    register(migration.deploy("CreditRedeem", hq), "CreditRedeem", 19)
    register(migration.deploy("TellerUtils", hq), "TellerUtils", 20)
    register(migration.deploy("EndaomentFunds", hq), "EndaomentFunds", 21)
    register(migration.deploy("EndaomentPSM", hq), "EndaomentPSM", 22)
