from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

users = [
    "0xE87a10d5B212D169CCBC9a50Cf5E23DD3da27cb6",
    "0xE5aB77408c25E7C1562C09067A8Fa3d0C00ac999",
    "0xdBab0B75921E3008Fd0bB621A8248D969d2d2F0d",
    "0xD7A48E684Da48cc384fD80bb1Fed7D8970bfe91b"
]


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    teller = migration.get_contract("Teller")

    auction_house = migration.get_contract("AuctionHouse")
    stability_pool = migration.get_contract("StabilityPool")


#    teller.liquidateManyUsers(users, sender=migration.account().address)
    # auction_house.liquidateManyUsers(users, migration.account().address, False, sender=teller.address)

    stability_pool.swapForLiquidatedCollateral(
        '0xaa0f13488CE069A7B5a099457c753A7CFBE04d36',
        0,
        '0x940181a94A35A4569E4529A3CDfB74e38FD98631',


        sender=auction_house.address
    )
