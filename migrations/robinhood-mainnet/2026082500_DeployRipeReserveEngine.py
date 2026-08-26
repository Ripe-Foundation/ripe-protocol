"""Deploy and print the Safe activation for the RH Ripe Reserve Engine.

Read ``migrate`` from top to bottom as the deployment checklist.  The deployer
only creates four paused contracts and relinquishes Foxtrot's temporary local
governance.  The live registries and Engine state change only through the Safe
batch printed at the end.

VaultMigrator is intentionally included and left paused.  RH currently ends at
RipeHq slot 24, while the merged protocol reserves slot 25 for VaultMigrator,
slot 26 for RipeReserveEngine, and slot 27 for RipeReserveVesting.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)


CANDIDATE_SUFFIX = "Candidate2026082500"

# Retained live RH generation.  These are checked before any deployment.
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
SWITCHBOARD_CHARLIE = "0x846176B2294a5168a04345087f0474738B569150"
MISSION_CONTROL = "0xD335373E59cA2F07FC3B779F2B456972C7EfDb29"
VAULT_BOOK = "0x9B37ea4E5b250Fef242fFC88364A143Fa39DF090"
RIPE_GOV = "0x7Eb9E83c4F475B650Ad25E359532286E130DED7f"
RIPE_TOKEN = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
ENDAOMENT_FUNDS = "0x84d022C46739dBEA862439f137eA3fF9752d4dfc"
ENDAOMENT_PSM = "0xbd8eE850965473a2E90c2C7096850f207D8Df986"
USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"

VAULT_MIGRATOR_ID = 25
RIPE_RESERVE_ENGINE_ID = 26
RIPE_RESERVE_VESTING_ID = 27
SWITCHBOARD_FOXTROT_ID = 6

ENGINE_CONFIG = (
    10_000_000,  # paymentCapPerEpoch: 10 USDG
    100_000,  # minPaymentAmount: 0.10 USDG
    8_000_000_000_000_000_000,  # maxAllInPayoutRate: 8 RIPE / USDG
    4_000_000_000_000_000_000,  # seedBasePayoutRate: 4 RIPE / USDG
    6_000,  # uHighBps: 60%
    4_000,  # uLowBps: 40%
    1_000,  # minUpBps: 10%
    3_000,  # maxUpBps: 30%
    300,  # minDownBps: 3%
    800,  # maxDownBps: 8%
    800,  # decayBps: 8% per skipped epoch
    4,  # maxDecayEpochs
    1_000,  # maxVestingBonus: 10%
    100,  # minVestingLength: 20 minutes
    600,  # maxVestingLength: 2 hours
    300,  # epochLength: 1 hour
)

ALLOCATION_BUDGET = 1_000 * 10**18
GENESIS_BLOCK = 0


def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    # ---------------------------------------------------------------------
    # 1. Verify the retained live topology and the four empty slots.
    # ---------------------------------------------------------------------
    log.h1("1. Checking the live RH registry slots")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    charlie = migration.get_contract("SwitchboardCharlie", SWITCHBOARD_CHARLIE)
    mission_control = migration.get_contract("MissionControl", MISSION_CONTROL)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    ripe_token = migration.get_contract("RipeToken", RIPE_TOKEN)
    endaoment_psm = migration.get_contract("EndaomentPSM", ENDAOMENT_PSM)

    assert address(hq.getAddr(3)) == address(ripe_token)
    assert address(hq.getAddr(5)) == address(mission_control)
    assert address(hq.getAddr(6)) == address(switchboard)
    assert address(hq.getAddr(8)) == address(vault_book)
    assert address(hq.getAddr(21)) == address(ENDAOMENT_FUNDS)
    assert address(hq.getAddr(22)) == address(endaoment_psm)
    assert address(switchboard.getAddr(3)) == address(charlie)
    assert address(endaoment_psm.USDC()) == address(USDG)
    assert not bool(ripe_token.isPaused())

    ripe_gov_id = int(mission_control.coreRipeGovVaultId())
    assert ripe_gov_id != 0
    assert address(vault_book.getAddr(ripe_gov_id)) == address(RIPE_GOV)
    assert bool(mission_control.isSupportedAssetInVault(ripe_gov_id, ripe_token))

    assert int(hq.numAddrs()) == VAULT_MIGRATOR_ID
    assert int(switchboard.numAddrs()) == SWITCHBOARD_FOXTROT_ID
    assert address(hq.getAddr(VAULT_MIGRATOR_ID)) == ZERO_ADDRESS
    assert address(hq.getAddr(RIPE_RESERVE_ENGINE_ID)) == ZERO_ADDRESS
    assert address(hq.getAddr(RIPE_RESERVE_VESTING_ID)) == ZERO_ADDRESS
    assert address(switchboard.getAddr(SWITCHBOARD_FOXTROT_ID)) == ZERO_ADDRESS

    # ---------------------------------------------------------------------
    # 2. Deploy the paused VaultMigrator, Engine, and Vesting contracts.
    # ---------------------------------------------------------------------
    log.h1("2. Deploying the paused departments")

    vault_migrator = migration.deploy(
        "VaultMigrator",
        hq,
        True,
        ZERO_ADDRESS,
        label=candidate("VaultMigrator"),
    )
    engine = migration.deploy(
        "RipeReserveEngine",
        hq,
        USDG,
        ENGINE_CONFIG,
        label=candidate("RipeReserveEngine"),
    )
    vesting = migration.deploy(
        "RipeReserveVesting",
        hq,
        label=candidate("RipeReserveVesting"),
    )

    assert bool(vault_migrator.isPaused())
    assert bool(engine.isPaused())
    assert bool(vesting.isPaused())
    assert not bool(engine.isRunning())
    assert not bool(engine.canAcquireRipe())
    assert address(engine.paymentToken()) == address(USDG)
    assert int(engine.paymentScale()) == 10**6
    assert tuple(map(int, engine.engineConfig())) == ENGINE_CONFIG

    # ---------------------------------------------------------------------
    # 3. Deploy Foxtrot with zero action delay and remove temporary gov.
    # ---------------------------------------------------------------------
    log.h1("3. Deploying SwitchboardFoxtrot")

    foxtrot = migration.deploy(
        "SwitchboardFoxtrot",
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=candidate("SwitchboardFoxtrot"),
    )
    assert int(foxtrot.actionTimeLock()) == 0
    relinquish_governance(migration, foxtrot)

    # ---------------------------------------------------------------------
    # 4. Print one atomic Safe batch that registers and starts the Engine.
    # ---------------------------------------------------------------------
    log.h1("4. Safe activation batch")
    print_safe_batch(vault_migrator, engine, vesting, foxtrot)


def address(value):
    return str(getattr(value, "address", value)).lower()


def relinquish_governance(migration, contract):
    assert address(contract.governance()) in (
        address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: address(contract.governance()) == ZERO_ADDRESS,
    )
    assert address(contract.governance()) == ZERO_ADDRESS


def print_safe_batch(vault_migrator, engine, vesting, foxtrot):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(f'const switchboard = c.Ripe_RH_Switchboard.at("{SWITCHBOARD}")')
    log.info(
        f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{SWITCHBOARD_CHARLIE}")'
    )
    log.info(
        f'const foxtrot = c.Ripe_RH_SwitchboardFoxtrot.at("{foxtrot.address}")'
    )
    log.info("")

    log.info("// Fill RipeHq slots 25, 26, and 27 in this exact order")
    for name, contract in (
        ("VaultMigrator", vault_migrator),
        ("RipeReserveEngine", engine),
        ("RipeReserveVesting", vesting),
    ):
        log.info(
            f'await hq.startAddNewAddressToRegistry("{contract.address}", "{name}")'
        )
        log.info(f'await hq.confirmNewAddressToRegistry("{contract.address}")')
    log.info("")

    log.info("// Register Foxtrot as Switchboard slot 6")
    log.info(
        "await switchboard.startAddNewAddressToRegistry("
        f'"{foxtrot.address}", "SwitchboardFoxtrot")'
    )
    log.info(
        f'await switchboard.confirmNewAddressToRegistry("{foxtrot.address}")'
    )
    log.info("")

    log.info("// Give only the Engine RIPE mint permission")
    log.info(
        "await hq.initiateHqConfigChange(26n, false, true, false)"
    )
    log.info("await hq.confirmHqConfigChange(26n)")
    log.info("")

    log.info("// Unpause Engine and Vesting; VaultMigrator remains paused")
    log.info(f'await charlie.pause("{engine.address}", false)')
    log.info(f'await charlie.pause("{vesting.address}", false)')
    log.info("")

    log.info("// Install the 1,000 RIPE budget with Foxtrot's zero delay")
    log.info(
        "await foxtrot.setReserveVestingRemainingAllocationBudget("
        f"{ALLOCATION_BUDGET}n)"
    )
    log.info("await foxtrot.executePendingAction(1n)")
    log.info("")

    log.info("// Enable and immediately start the Engine; no rate override")
    log.info("await foxtrot.setCanAcquireRipe(true)")
    log.info(f"await foxtrot.startReserveEngine({GENESIS_BLOCK}n, 300n)")
    log.info("")
    log.info("// Then run migration 2026082501 to verify and promote.")
