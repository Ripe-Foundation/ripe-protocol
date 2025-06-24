from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Auction House")

    auction_house_nft = migration.deploy(
        "AuctionHouseNFT",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, auction_house_nft, "Auction House NFT")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, auction_house_nft)) == 10
