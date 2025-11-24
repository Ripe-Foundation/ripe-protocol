from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):

    pd = migration.get_contract("PriceDesk", '0xDFe8D79bc05420a3fFa14824135016a738eE8299')
    print("Current Price Desk address:", pd.address)

    blueprint = migration.blueprint()

    price_desk = migration.deploy(
        "PriceDesk",
        migration.get_address("RipeHq"),
        migration.account(),
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    for i in range(pd.numAddrs()):
        source = pd.getAddrInfo(i+1)
        if source.addr == ZERO_ADDRESS:
            continue
        print(i+1)
        print('addr:', source.addr)
        print('desc:', source.description)
        print('--------------------------------')

        migration.execute(price_desk.startAddNewAddressToRegistry, source.addr, source.description)
        assert int(migration.execute(price_desk.confirmNewAddressToRegistry, source.addr)) == i+1

    price_desk = migration.execute(price_desk.relinquishGov)
