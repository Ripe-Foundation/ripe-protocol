from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):

    pd = migration.get_contract("PriceDesk", '0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6')
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
        addr = source.addr
        if source.addr == ZERO_ADDRESS and i == 2:
            addr = '0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6'
        elif source.addr == ZERO_ADDRESS:
            continue
        print(i+1)
        print('addr:', source.addr)
        print('desc:', source.description)
        print('--------------------------------')

        migration.execute(price_desk.startAddNewAddressToRegistry, addr, source.description)
        assert int(migration.execute(price_desk.confirmNewAddressToRegistry, addr)) == i+1

    migration.execute(price_desk.startAddressDisableInRegistry, 3)
    migration.execute(price_desk.confirmAddressDisableInRegistry, 3)
    price_desk = migration.execute(price_desk.relinquishGov)
