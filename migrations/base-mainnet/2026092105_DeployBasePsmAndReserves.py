"""Stage PSM and dormant USDC reserves; do not transfer treasury or vault funds."""

from scripts.utils import log
from scripts.utils.migration import Migration

HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
SUFFIX = "BaseDepartments20260921"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
# Constructor-valid placeholders only, not approved sale economics. The engine
# remains paused, unregistered and unfunded until governance configures launch.
DORMANT_CONFIG = (
    1_000_000, 1_000_000, 10**18, 10**18,
    6000, 4000, 1000, 3000, 300, 800, 800, 4,
    0, 43_200, 1_296_000, 43_200,
)


def migrate(migration: Migration):
    assert migration.chain() == "base-mainnet"
    hq = migration.get_contract("RipeHq")
    assert str(hq.address).lower() == HQ
    active = [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))]
    assert hq.numAddrs() == 25, "review reserved future HQ IDs 25-27"
    book = migration.get_contract("VaultBook", hq.getAddr(8))
    old = migration.get_contract("EndaomentPSM", hq.getAddr(22))
    assert str(old.USDC()).lower() == USDC
    fields = ("numBlocksPerInterval", "mintFee", "maxIntervalMint", "redeemFee", "maxIntervalRedeem")
    config = tuple(getattr(old, name)() for name in fields)
    yield_position = tuple(old.usdcYieldPosition())

    log.h1("1. Deploy PSM with the live USDC limits and yield destination")
    psm = migration.deploy(
        "EndaomentPSM", hq.address, *config, old.USDC(), *yield_position,
        label="EndaomentPSM" + SUFFIX,
    )
    assert tuple(getattr(psm, name)() for name in fields) == config
    assert tuple(psm.usdcYieldPosition()) == yield_position
    assert not psm.canMint() and not psm.canRedeem()

    log.h1("2. Deploy paused migrator and USDC reserve contracts")
    migrator = migration.deploy(
        "VaultMigrator", hq.address, True, book.getAddr(2), label="VaultMigrator" + SUFFIX,
    )
    engine = migration.deploy(
        "RipeReserveEngine", hq.address, old.USDC(), DORMANT_CONFIG,
        label="RipeReserveEngine" + SUFFIX,
    )
    vesting = migration.deploy("RipeReserveVesting", hq.address, label="RipeReserveVesting" + SUFFIX)
    assert migrator.isPaused() and engine.isPaused() and vesting.isPaused()
    assert not engine.isRunning() and not engine.canAcquireRipe()
    assert tuple(engine.engineConfig()) == DORMANT_CONFIG
    assert [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))] == active
    for name, candidate, slot in (
        ("EndaomentPSM", psm, 22), ("VaultMigrator", migrator, 25),
        ("RipeReserveEngine", engine, 26), ("RipeReserveVesting", vesting, 27),
    ):
        log.info(f"STAGED {name} (future HQ slot {slot}): {candidate.address}")
    log.info("No HQ registrations or funds moves. Future new HQ IDs must be assigned 25, 26, 27 in order.")
    log.info("Before cutover: migrate PSM/EndaomentFunds assets; review all mutable policy.")
    log.info("PSM redemption/allowlist testing and reserve launch configuration require separate governance.")
