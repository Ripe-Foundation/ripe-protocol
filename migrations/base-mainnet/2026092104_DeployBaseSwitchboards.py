"""Stage a populated Switchboard, preserving the already deployed Foxtrot."""

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
SUFFIX = "BaseDepartments20260921"
NAMES = ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf")


def migrate(migration: Migration):
    assert migration.chain() == "base-mainnet"
    hq = migration.get_contract("RipeHq")
    assert str(hq.address).lower() == HQ
    active = hq.getAddr(6)
    old = migration.get_contract("Switchboard", active)
    assert old.numAddrs() == 7, "review changed live controller topology"
    rows = [tuple(old.addrInfo(i)) for i in range(1, 7)]
    fox = migration.get_contract("SwitchboardFoxtrotBaseConfig20260921")
    assert str(old.getAddr(6)).lower() == str(fox.address).lower()
    params = migration.blueprint().PARAMS
    assert params["PYTH_PRICES_ID"] == 4

    log.h1("1. Deploy the other six controllers with zero action timelocks")
    new = {"Foxtrot": fox}
    for name in NAMES:
        if name == "Foxtrot":
            continue  # Preserve MC initialization progress and rewards binding.
        if name == "Golf":
            bounds = (params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"], params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"])
        else:
            live = migration.get_contract("Switchboard" + name, rows[NAMES.index(name)][0])
            bounds = (live.minActionTimeLock(), live.maxActionTimeLock())
        args = (hq.address, ZERO, *bounds)
        if name == "Alpha":
            args = (hq.address, ZERO, params["PRICE_DESK_MIN_STALE_TIME"],
                    params["PRICE_DESK_MAX_STALE_TIME"], *bounds, 4)
        new[name] = migration.deploy("Switchboard" + name, *args, label="Switchboard" + name + SUFFIX)
        assert new[name].actionTimeLock() == 0

    log.h1("2. Deploy and populate the inactive registry")
    board = migration.deploy(
        "Switchboard", hq.address, migration.account(),
        old.minRegistryTimeLock(), old.maxRegistryTimeLock(), label="Switchboard" + SUFFIX,
    )
    for i, name in enumerate(NAMES, 1):
        migration.execute(board.startAddNewAddressToRegistry, new[name].address, "Switchboard " + name)
        migration.execute(board.confirmNewAddressToRegistry, new[name].address)
        assert board.getAddr(i) == new[name].address
        assert board.getRegId(new[name].address) == i
    migration.execute(board.relinquishGov)
    assert str(board.governance()).lower() == ZERO
    assert board.registryChangeTimeLock() == 0 and board.numAddrs() == 8
    assert hq.getAddr(6) == active
    assert [tuple(old.addrInfo(i)) for i in range(1, 7)] == rows
    log.info(f"STAGED Switchboard (HQ slot 6): {board.address}")
    log.info("Foxtrot retained at ID 6; Golf added at ID 7. No controller was activated.")
    log.info("Reconcile pending actions on replaced controllers before activation; they are not copied.")
