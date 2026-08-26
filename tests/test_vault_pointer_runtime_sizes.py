import boa

EIP170_LIMIT = 24_576

# Exact deployed runtimes at this head (boa, including immutables).
# These are a drift tripwire: an unintended size change fails as a
# dict diff instead of waiting for the EIP-170 cliff. Update the pin
# when a size change is intentional. vyper==0.4.3 / titanoboa==0.2.7
# are load-bearing for these numbers — bumping either is a deploy event.
# RipeGov headroom is 460 bytes after the migration, SharesVault, and
# governance-remediation changes. Any RipeGov edit must remeasure this pin.
# Composed SwitchboardAlpha headroom is 14 bytes after binding its chain-local
# Pyth source ID. Teller and CreditEngine retain 24 and 33 bytes respectively at
# this head. Endaoment retains 1,190 bytes after binding its chain-local Curve
# source ID. These pins include the deployed immutable data.
# Lootbox headroom is 120 bytes at the pinned 24,456-byte deployed runtime
# after removing the non-shippable global-deposit settle selector. Any Lootbox
# edit, however small, must recompile and remeasure this pin before merge;
# its `# pragma optimize codesize` (no CLI -O override) is load-bearing.
# MissionControl 17,178 / Ledger 13,306 after removing reward-settle
# orchestration, preserving the legacy delivery-config getters, adding compact
# effective-delivery getters and the compact retirement-config getter, and
# restoring Ledger to its deployable interface. DefaultsLocal is 1,200 bytes
# (points enabled to match production).
# StabilityPool headroom is 242 bytes after the actual-delivery claim,
# separate $0.02 full-exit tolerance and $0.05 retention threshold, and
# redemption hardening, deferred claim checkpoint, claimable-aware retirement,
# and partial-reservation admission remediations.
# Any StabilityPool or StabVault edit must recompile and remeasure this pin
# before merge.
# SwitchboardBravo retains 399 bytes of headroom after removing the
# live-allocation freeze. CreditRedeem retains 16,094 bytes after consuming MissionControl's
# effective redemption-delivery flag. AuctionHouse retains 46 bytes after the
# compact effective auction-delivery config; unsupported collateral is delivered
# externally, while the dedicated auction/redemption flags govern those paths.
# Deleverage retains 39 bytes. CurvePrices retains 1,170 bytes after switching
# to codesize optimization for confirmation-time registry snapshot checks.
# UndyVaultPrices retains 6,270 bytes after confirmation-time metadata
# binding and checked runtime arithmetic. Any edit to these contracts must
# recompile and remeasure.
EXPECTED_RUNTIME_BYTES = {
    "MissionControl": 17178,
    "DefaultsLocal": 1200,
    "SwitchboardAlpha": 24562,
    "SwitchboardBravo": 24177,
    "SwitchboardCharlie": 24211,
    "SwitchboardEcho": 23930,
    "VaultMigrator": 15626,
    "VaultBook": 14410,
    "Teller": 24552,
    "TellerUtils": 9113,
    "BondRoom": 10927,
    "Ledger": 13306,
    "Lootbox": 24456,
    "GreenToken": 8760,
    "SavingsGreen": 13166,
    "RipeToken": 8760,
    "RebaseErc20": 11602,
    "RipeGov": 24116,
    "HumanResources": 14932,
    "AuctionHouse": 24530,
    "CreditEngine": 24543,
    "CreditRedeem": 8482,
    "Endaoment": 23386,
    "PriceDesk": 17742,
    "Deleverage": 24537,
    "StabilityPool": 24334,
    "BlueChipYieldPrices": 20857,
    "ChainlinkPrices": 16672,
    "CurvePrices": 23406,
    "PythPrices": 16055,
    "RedStone": 15325,
    "StorkPrices": 15067,
    "UndyVaultPrices": 18306,
    "wsuperOETHbPrices": 8336,
}


def test_pointer_changed_contracts_fit_eip170_deployed_runtime_limit(
    mission_control,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    switchboard_echo,
    vault_migrator,
    vault_book,
    teller,
    teller_utils,
    bond_room,
    ledger,
    lootbox,
    green_token,
    savings_green,
    ripe_token,
    rebase_erc20_vault,
    ripe_gov_vault,
    human_resources,
    auction_house,
    credit_engine,
    credit_redeem,
    endaoment,
    price_desk,
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
    defaults_local = boa.load("contracts/config/DefaultsLocal.vy")
    deployed_runtime_bytes = {
        "MissionControl": len(mission_control.env.get_code(mission_control.address)),
        "DefaultsLocal": len(defaults_local.env.get_code(defaults_local.address)),
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
        "VaultBook": len(vault_book.env.get_code(vault_book.address)),
        "Teller": len(teller.env.get_code(teller.address)),
        "TellerUtils": len(teller_utils.env.get_code(teller_utils.address)),
        "BondRoom": len(bond_room.env.get_code(bond_room.address)),
        "Ledger": len(ledger.env.get_code(ledger.address)),
        "Lootbox": len(lootbox.env.get_code(lootbox.address)),
        "GreenToken": len(green_token.env.get_code(green_token.address)),
        "SavingsGreen": len(savings_green.env.get_code(savings_green.address)),
        "RipeToken": len(ripe_token.env.get_code(ripe_token.address)),
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
        "Endaoment": len(endaoment.env.get_code(endaoment.address)),
        "PriceDesk": len(price_desk.env.get_code(price_desk.address)),
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
        if size > EIP170_LIMIT
    }
    assert not oversized, f"EIP-170 runtime limit exceeded: {oversized}"
    assert headroom["SwitchboardBravo"] >= 200, (
        "SwitchboardBravo must keep at least 200 bytes of EIP-170 headroom: "
        f"{headroom['SwitchboardBravo']}"
    )
    runtime_diff = {
        name: (
            EXPECTED_RUNTIME_BYTES.get(name),
            deployed_runtime_bytes.get(name),
        )
        for name in sorted(EXPECTED_RUNTIME_BYTES.keys() | deployed_runtime_bytes.keys())
        if EXPECTED_RUNTIME_BYTES.get(name) != deployed_runtime_bytes.get(name)
    }
    assert not runtime_diff, (
        "Deployed runtime changed; update EXPECTED_RUNTIME_BYTES if intentional: "
        f"{runtime_diff}"
    )
