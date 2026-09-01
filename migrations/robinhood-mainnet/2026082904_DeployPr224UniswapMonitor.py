"""Deploy PR #224's monitor plus an sNET rebase vault and print the Safe batch.

The monitor stays bound to the live RIPE/NVDA pair for the existing convenience
views, while PR #224 adds the stateless getPoolMonitoringPrice() entry point.
The deployer deploys the monitor and a new RebaseErc20 vault. Governance
registers the vault, rotates PriceDesk slot 3, retires wsNET, and registers
sNET plus QUOTRONS through the printed Safe calls.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
MISSION_CONTROL = "0x6445Faf17Bf8CE20ea8f038E028078F1E6B87faC"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
SWITCHBOARD_BRAVO = "0x20857b906A5C35EFcae98bAfC83fEF91B5f49B1b"
SWITCHBOARD_CHARLIE = "0x27bC3A748d363f27094e0D21c7fDF4F42bf64c0F"
TRAINING_WHEELS = "0x987DEa46AEfA442B67Faa5Db6F71024e5be01406"

RIPE = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
NVDA = "0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC"
RIPE_NVDA_POOL = "0x9b8537bE0FD5cf9B2AD495C5A85130D5bAe4769D"
CURRENT_MONITOR = "0x6CA83A04BCF7651fFB0D2D1ab4376E8EC3b91d89"
COMMUNITY_VAULT = "0xABc93b41fB9B7f03F63d93e0e80e149F201D4b36"

WSNET = "0x63C12667638f2Ae6fC6ae09B43D98Ec84a8586eA"
SNET = "0xb773ec2C326B7f98a5a83fc098825492F020a4c7"
QUOTRONS = "0x5a86828efd322bfb16d93cfed16ee9bc14940d7f"

UNISWAP_MONITOR_ID = 3
COMMUNITY_VAULT_ID = 4
REBASE_VAULT_ID = 5
VOTER_POINTS_ALLOCATION = 1_000
LABEL = "UniswapV2PricesNvda"

# Preserve the Community vault's human limits while respecting token decimals.
ASSETS = (
    # address, symbol, decimals, vault id
    (SNET, "sNET", 9, REBASE_VAULT_ID),
    (QUOTRONS, "QUOTRONS", 18, COMMUNITY_VAULT_ID),
)


def migrate(migration: Migration):
    log.h1("1. Checking the live monitor and asset state")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    mission_control = migration.get_contract(
        "MissionControl", MISSION_CONTROL
    )
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    ripe = migration.get_contract("RipeToken", RIPE)

    assert address(hq.getAddr(5)) == address(mission_control)
    assert address(hq.getAddr(7)) == address(price_desk)
    assert address(hq.getAddr(8)) == address(vault_book)
    assert int(vault_book.numAddrs()) == REBASE_VAULT_ID
    assert address(vault_book.getAddr(COMMUNITY_VAULT_ID)) == address(
        COMMUNITY_VAULT
    )
    assert address(price_desk.getAddr(UNISWAP_MONITOR_ID)) == address(
        CURRENT_MONITOR
    )
    assert bool(mission_control.isSupportedAsset(WSNET))
    assert not bool(mission_control.isSupportedAsset(SNET))
    assert not bool(mission_control.isSupportedAsset(QUOTRONS))

    log.h1("2. Deploying PR #224 monitor and the sNET rebase vault")

    monitor = migration.deploy(
        "UniswapV2Prices",
        hq,
        RIPE_NVDA_POOL,
        ripe,
        NVDA,
        label=LABEL,
    )
    rebase_vault = migration.deploy("RebaseErc20", hq)

    assert bool(monitor.isMonitoringOnly())
    assert address(monitor.RIPE_HQ()) == address(hq)
    assert address(monitor.RIPE_WETH_POOL()) == address(RIPE_NVDA_POOL)
    assert address(monitor.RIPE_TOKEN()) == address(ripe)
    assert address(monitor.WETH_TOKEN()) == address(NVDA)
    assert int(monitor.getRipeUsdMonitoringPrice()) != 0
    assert int(
        monitor.getPoolMonitoringPrice(RIPE, RIPE_NVDA_POOL, NVDA)
    ) == int(monitor.getRipeUsdMonitoringPrice())
    assert monitor.getPriceAndHasFeed(ripe.address) == (0, False)
    assert int(vault_book.getRegId(rebase_vault)) == 0

    log.h1("3. Atomic Safe update")
    print_safe_batch(monitor, rebase_vault)


def print_safe_batch(monitor, rebase_vault):
    log.info(f'const priceDesk = c.Ripe_RH_PriceDesk.at("{PRICE_DESK}")')
    log.info(f'const vaultBook = c.Ripe_RH_VaultBook.at("{VAULT_BOOK}")')
    log.info(
        'const bravo = c.Ripe_RH_SwitchboardBravo.at('
        f'"{SWITCHBOARD_BRAVO}")'
    )
    log.info(
        'const charlie = c.Ripe_RH_SwitchboardCharlie.at('
        f'"{SWITCHBOARD_CHARLIE}")'
    )
    log.info("const zeroAddress = \"0x0000000000000000000000000000000000000000\"")
    log.info("const zeroDebtTerms = [0n, 0n, 0n, 0n, 0n, 0n]")
    log.info("let bravoActionId = await bravo.actionId()")
    log.info("let charlieActionId = await charlie.actionId()")
    log.info("")

    log.info("// 1. Register the dedicated sNET rebase vault as VaultBook id 5")
    log.info(
        "await vaultBook.startAddNewAddressToRegistry("
        f'"{rebase_vault.address}", "RebaseErc20")'
    )
    log.info(
        "await vaultBook.confirmNewAddressToRegistry("
        f'"{rebase_vault.address}")'
    )
    log.info("")

    log.info("// 2. Activate the PR #224 monitor in the existing UI slot")
    log.info(
        "await priceDesk.startAddressUpdateToRegistry("
        f'{UNISWAP_MONITOR_ID}n, "{monitor.address}")'
    )
    log.info(
        "await priceDesk.confirmAddressUpdateToRegistry("
        f"{UNISWAP_MONITOR_ID}n)"
    )
    log.info("")

    log.info("// 3. Retire wsNET while preserving its withdrawal exit")
    log.info(f'await charlie.setCanDepositAsset("{WSNET}", false)')
    log.info(f'await charlie.setCanClaimInStabPoolAsset("{WSNET}", true)')
    log.info(f'await bravo.setWhitelistForAsset("{WSNET}", zeroAddress)')
    log.info("await bravo.executePendingAction(bravoActionId)")
    log.info("bravoActionId += 1n")
    log.info(f'await charlie.setRewardVaultId("{WSNET}", 0n)')
    log.info("await charlie.executePendingAction(charlieActionId)")
    log.info("charlieActionId += 1n")
    log.info(f'await charlie.deregisterAsset("{WSNET}")')
    log.info("await charlie.executePendingAction(charlieActionId)")
    log.info("charlieActionId += 1n")
    log.info("")

    log.info("// 4. Add sNET to vault 5 and QUOTRONS to Community vault 4")
    for asset, symbol, decimals, vault_id in ASSETS:
        unit = 10**decimals
        per_user_limit = 100_000_000 * unit
        global_limit = 1_000_000_000 * unit
        min_deposit_balance = unit // 1_000

        log.info(f"// {symbol} ({decimals} decimals, vault {vault_id})")
        log.info("await bravo.addAsset(")
        log.info(f'    "{asset}", [{vault_id}n],')
        log.info("    0n, 0n,")
        log.info(
            f"    {per_user_limit}n, {global_limit}n, "
            f"{min_deposit_balance}n,"
        )
        log.info("    zeroDebtTerms,")
        log.info("    false, false, false, false,")
        log.info("    true, true, false, false, false, false, 0n")
        log.info(")")
        log.info("await bravo.executePendingAction(bravoActionId)")
        log.info("bravoActionId += 1n")
        log.info(
            f'await bravo.setWhitelistForAsset("{asset}", '
            f'"{TRAINING_WHEELS}")'
        )
        log.info("await bravo.executePendingAction(bravoActionId)")
        log.info("bravoActionId += 1n")
        log.info("await bravo.setAssetDepositParams(")
        log.info(f'    "{asset}", [{vault_id}n],')
        log.info(f"    0n, {VOTER_POINTS_ALLOCATION}n,")
        log.info(
            f"    {per_user_limit}n, {global_limit}n, "
            f"{min_deposit_balance}n"
        )
        log.info(")")
        log.info("await bravo.executePendingAction(bravoActionId)")
        log.info("bravoActionId += 1n")
        log.info("")


def address(value):
    return str(getattr(value, "address", value)).lower()
