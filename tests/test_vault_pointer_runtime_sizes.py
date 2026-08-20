EIP170_LIMIT = 24_576

# Exact deployed runtimes at this head (boa, including immutables).
# These are a drift tripwire: an unintended size change fails as a
# dict diff instead of waiting for the EIP-170 cliff. Update the pin
# when a size change is intentional. vyper==0.4.3 / titanoboa==0.2.7
# are load-bearing for these numbers — bumping either is a deploy event.
# RipeGov headroom is ~846 bytes after removing areKeyTermsSame. Any RipeGov
# edit must remeasure this pin before merge.
# Lootbox headroom is exactly 120 bytes at this candidate head. Any Lootbox
# edit, however small, must recompile and remeasure this pin before merge;
# its `# pragma optimize codesize` (no CLI -O override) is load-bearing.
EXPECTED_RUNTIME_BYTES = {
    "MissionControl": 16143,
    "SwitchboardAlpha": 24521,
    "SwitchboardBravo": 24364,
    "SwitchboardCharlie": 23873,
    "SwitchboardEcho": 23192,
    "VaultMigrator": 12464,
    "Teller": 24556,
    "TellerUtils": 9113,
    "BondRoom": 10927,
    "Ledger": 13306,
    "Lootbox": 24456,
    "RebaseErc20": 11411,
    "RipeGov": 23730,
    "HumanResources": 13292,
    "AuctionHouse": 24528,
    "CreditEngine": 24502,
    "CreditRedeem": 8303,
    "Deleverage": 24459,
    "StabilityPool": 24269,
    "BlueChipYieldPrices": 22749,
    "ChainlinkPrices": 14256,
    "CurvePrices": 23141,
    "PythPrices": 14282,
    "RedStone": 13633,
    "StorkPrices": 13162,
    "UndyVaultPrices": 17612,
    "wsuperOETHbPrices": 8763,
}


def test_pointer_changed_contracts_fit_eip170_deployed_runtime_limit(
    mission_control,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    switchboard_echo,
    vault_migrator,
    teller,
    teller_utils,
    bond_room,
    ledger,
    lootbox,
    rebase_erc20_vault,
    ripe_gov_vault,
    human_resources,
    auction_house,
    credit_engine,
    credit_redeem,
    deleverage,
    stability_pool,
    blue_chip_prices,
    chainlink,
    curve_prices,
    pyth_prices,
    redstone,
    stork_prices,
    undy_vault_prices,
    wsuper_oethb_prices,
):
    deployed_runtime_bytes = {
        "MissionControl": len(mission_control.env.get_code(mission_control.address)),
        "SwitchboardAlpha": len(
            switchboard_alpha.env.get_code(switchboard_alpha.address)
        ),
        "SwitchboardBravo": len(
            switchboard_bravo.env.get_code(switchboard_bravo.address)
        ),
        "SwitchboardCharlie": len(
            switchboard_charlie.env.get_code(switchboard_charlie.address)
        ),
        "SwitchboardEcho": len(
            switchboard_echo.env.get_code(switchboard_echo.address)
        ),
        "VaultMigrator": len(vault_migrator.env.get_code(vault_migrator.address)),
        "Teller": len(teller.env.get_code(teller.address)),
        "TellerUtils": len(teller_utils.env.get_code(teller_utils.address)),
        "BondRoom": len(bond_room.env.get_code(bond_room.address)),
        "Ledger": len(ledger.env.get_code(ledger.address)),
        "Lootbox": len(lootbox.env.get_code(lootbox.address)),
        "RebaseErc20": len(
            rebase_erc20_vault.env.get_code(rebase_erc20_vault.address)
        ),
        "RipeGov": len(ripe_gov_vault.env.get_code(ripe_gov_vault.address)),
        "HumanResources": len(
            human_resources.env.get_code(human_resources.address)
        ),
        "AuctionHouse": len(auction_house.env.get_code(auction_house.address)),
        "CreditEngine": len(credit_engine.env.get_code(credit_engine.address)),
        "CreditRedeem": len(credit_redeem.env.get_code(credit_redeem.address)),
        "Deleverage": len(deleverage.env.get_code(deleverage.address)),
        "StabilityPool": len(stability_pool.env.get_code(stability_pool.address)),
        "BlueChipYieldPrices": len(blue_chip_prices.env.get_code(blue_chip_prices.address)),
        "ChainlinkPrices": len(chainlink.env.get_code(chainlink.address)),
        "CurvePrices": len(curve_prices.env.get_code(curve_prices.address)),
        "PythPrices": len(pyth_prices.env.get_code(pyth_prices.address)),
        "RedStone": len(redstone.env.get_code(redstone.address)),
        "StorkPrices": len(stork_prices.env.get_code(stork_prices.address)),
        "UndyVaultPrices": len(undy_vault_prices.env.get_code(undy_vault_prices.address)),
        "wsuperOETHbPrices": len(wsuper_oethb_prices.env.get_code(wsuper_oethb_prices.address)),
    }
    print("DEPLOYED_RUNTIME_BYTES", deployed_runtime_bytes)

    headroom = {
        name: EIP170_LIMIT - size for name, size in deployed_runtime_bytes.items()
    }
    print("DEPLOYED_RUNTIME_HEADROOM", headroom)

    oversized = {
        name: size
        for name, size in deployed_runtime_bytes.items()
        if size >= EIP170_LIMIT
    }
    assert not oversized, f"EIP-170 runtime limit reached or exceeded: {oversized}"
    assert deployed_runtime_bytes == EXPECTED_RUNTIME_BYTES, (
        "Deployed runtime changed; update EXPECTED_RUNTIME_BYTES if intentional: "
        f"{ {k: (EXPECTED_RUNTIME_BYTES[k], deployed_runtime_bytes[k]) for k in deployed_runtime_bytes if EXPECTED_RUNTIME_BYTES.get(k) != deployed_runtime_bytes[k]} }"
    )
