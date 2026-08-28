"""Deploy the RIPE/NVDA UI monitor and print the LP rotation Safe batch.

The deployed contract is the existing, unchanged UniswapV2Prices monitor.
NVDA occupies its legacy WETH constructor slot, so the UI's existing
getRipeUsdMonitoringPrice() integration continues to work without a new ABI.

The deployer does not mutate protocol configuration.  Governance performs the
complete reward/deposit rotation through the readable Safe batch printed last.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
MISSION_CONTROL = "0xC154F6fCA0788947E49Ffb4AD121F03C8332EFDe"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
SWITCHBOARD_ALPHA = "0xc36b4E857A6430e0D848eaA3C664B855F804Cc26"
SWITCHBOARD_BRAVO = "0xd7F1d8BBB1f06879fBbdda695d35C5aa0117394f"
SWITCHBOARD_CHARLIE = "0xc4d4E0EBC6b40FC31893449327E7080feE2CEA20"
TELLER = "0x2D3Cb2B39289f402187D7DC9B609ead6646f2506"

RIPE = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
NVDA = "0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC"
RIPE_WETH_POOL = "0xba6F6CBa1a4104000847d4fdccB676E99166CEcE"
RIPE_NVDA_POOL = "0x9b8537bE0FD5cf9B2AD495C5A85130D5bAe4769D"

OLD_UNISWAP_MONITOR = "0x65D6e4b6406eFe2D56f87FBA2adCE6eDB5AC0d83"
UNISWAP_MONITOR_ID = 3
RIPE_GOV_VAULT_ID = 2

# Preserve the live RIPE/WETH deposit policy for the replacement LP.
PER_USER_DEPOSIT_LIMIT = 100_000_000 * 10**18
GLOBAL_DEPOSIT_LIMIT = 1_000_000_000 * 10**18
MIN_DEPOSIT_BALANCE = 10**15

# Preserve the live RIPE/WETH RipeGov terms.
ASSET_WEIGHT = 15_000
MAX_LOCK_DURATION = 7_884_000
MAX_LOCK_BOOST = 20_000
EXIT_FEE = 8_000

REWARD_ALLOCATION = 2_500
INITIAL_DEPOSIT = MIN_DEPOSIT_BALANCE
LABEL = "UniswapV2PricesNvda"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Read the exact live contracts this change builds on.
    # ------------------------------------------------------------------
    log.h1("1. Checking the live RIPE LP topology")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    mission_control = migration.get_contract(
        "MissionControl", MISSION_CONTROL
    )
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    ripe = migration.get_contract("RipeToken", RIPE)

    assert address(hq.getAddr(5)) == address(mission_control)
    assert address(hq.getAddr(7)) == address(price_desk)
    assert address(price_desk.getAddr(UNISWAP_MONITOR_ID)) == address(
        OLD_UNISWAP_MONITOR
    )
    assert bool(mission_control.isSupportedAsset(RIPE_WETH_POOL))
    assert not bool(mission_control.isSupportedAsset(RIPE_NVDA_POOL))

    # ------------------------------------------------------------------
    # 2. Deploy the unchanged monitor against RIPE/NVDA.
    # ------------------------------------------------------------------
    log.h1("2. Deploying UniswapV2Prices for RIPE/NVDA")

    monitor = migration.deploy(
        "UniswapV2Prices",
        hq,
        RIPE_NVDA_POOL,
        ripe,
        NVDA,
        label=LABEL,
    )

    assert bool(monitor.isMonitoringOnly())
    assert address(monitor.RIPE_HQ()) == address(hq)
    assert address(monitor.RIPE_WETH_POOL()) == address(RIPE_NVDA_POOL)
    assert address(monitor.RIPE_TOKEN()) == address(ripe)
    assert address(monitor.WETH_TOKEN()) == address(NVDA)
    assert int(monitor.getRipeWethMonitoringPrice()) != 0
    assert int(monitor.getRipeUsdMonitoringPrice()) != 0
    assert monitor.getPriceAndHasFeed(ripe.address) == (0, False)

    # ------------------------------------------------------------------
    # 3. Print the atomic UI pointer and protocol configuration batch.
    # ------------------------------------------------------------------
    log.h1("3. Atomic Safe update")
    print_safe_batch(monitor)


def print_safe_batch(monitor):
    log.info(f'const priceDesk = c.Ripe_RH_PriceDesk.at("{PRICE_DESK}")')
    log.info(
        f'const alpha = c.Ripe_RH_SwitchboardAlpha.at("{SWITCHBOARD_ALPHA}")'
    )
    log.info(
        f'const bravo = c.Ripe_RH_SwitchboardBravo.at("{SWITCHBOARD_BRAVO}")'
    )
    log.info(
        f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{SWITCHBOARD_CHARLIE}")'
    )
    log.info(f'const teller = c.Ripe_RH_Teller.at("{TELLER}")')
    log.info(
        f'const ripeNvdaLp = c.UniswapV2Pair.at("{RIPE_NVDA_POOL}")'
    )
    log.info("const firstBravoActionId = await bravo.actionId()")
    log.info("const alphaActionId = await alpha.actionId()")
    log.info("const zeroDebtTerms = [0n, 0n, 0n, 0n, 0n, 0n]")
    log.info("")

    log.info("// 1. Point the UI monitor slot from RIPE/WETH to RIPE/NVDA")
    log.info(
        "await priceDesk.startAddressUpdateToRegistry("
        f'{UNISWAP_MONITOR_ID}n, "{monitor.address}")'
    )
    log.info(
        f"await priceDesk.confirmAddressUpdateToRegistry({UNISWAP_MONITOR_ID}n)"
    )
    log.info("")

    log.info("// 2. Remove RIPE/WETH's 25% reward allocation")
    log.info(
        "await bravo.setAssetDepositParams("
        f'"{RIPE_WETH_POOL}", [{RIPE_GOV_VAULT_ID}n], 0n, 0n, '
        f"{PER_USER_DEPOSIT_LIMIT}n, {GLOBAL_DEPOSIT_LIMIT}n, "
        f"{MIN_DEPOSIT_BALANCE}n)"
    )
    log.info("await bravo.executePendingAction(firstBravoActionId)")
    log.info("")

    log.info("// 3. Disable RIPE/WETH deposits without removing vault 2")
    log.info(f'await charlie.setCanDepositAsset("{RIPE_WETH_POOL}", false)')
    log.info("")

    log.info("// 4. Add RIPE/NVDA to RipeGov, initially with zero rewards")
    log.info("await bravo.addAsset(")
    log.info(f'    "{RIPE_NVDA_POOL}",')
    log.info(f"    [{RIPE_GOV_VAULT_ID}n],")
    log.info("    0n, 0n,")
    log.info(
        f"    {PER_USER_DEPOSIT_LIMIT}n, {GLOBAL_DEPOSIT_LIMIT}n, "
        f"{MIN_DEPOSIT_BALANCE}n,"
    )
    log.info("    zeroDebtTerms,")
    log.info("    false, false, false, false,")
    log.info("    true, true, false")
    log.info(")")
    log.info("await bravo.executePendingAction(firstBravoActionId + 1n)")
    log.info("")

    log.info("// 5. Give RIPE/NVDA the old LP's lock and weighting terms")
    log.info("await alpha.setRipeGovVaultConfig(")
    log.info(f'    "{RIPE_NVDA_POOL}",')
    log.info(f"    {ASSET_WEIGHT}n, true, 0n, {MAX_LOCK_DURATION}n,")
    log.info(f"    {MAX_LOCK_BOOST}n, {EXIT_FEE}n, true")
    log.info(")")
    log.info("await alpha.executePendingAction(alphaActionId)")
    log.info("")

    log.info("// 6. Initialize its reward row with 0.001 governance LP")
    log.info(f'await ripeNvdaLp.approve("{TELLER}", {INITIAL_DEPOSIT}n)')
    log.info(
        f'await teller.depositIntoGovVault("{RIPE_NVDA_POOL}", '
        f"{INITIAL_DEPOSIT}n, 0n)"
    )
    log.info("")

    log.info("// 7. Move the 25% reward allocation to RIPE/NVDA")
    log.info(
        "await bravo.setAssetDepositParams("
        f'"{RIPE_NVDA_POOL}", [{RIPE_GOV_VAULT_ID}n], '
        f"{REWARD_ALLOCATION}n, 0n, {PER_USER_DEPOSIT_LIMIT}n, "
        f"{GLOBAL_DEPOSIT_LIMIT}n, {MIN_DEPOSIT_BALANCE}n)"
    )
    log.info("await bravo.executePendingAction(firstBravoActionId + 2n)")


def address(value):
    return str(getattr(value, "address", value)).lower()
