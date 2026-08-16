EIP170_LIMIT = 24_576


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
    stability_pool,
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
        "StabilityPool": len(stability_pool.env.get_code(stability_pool.address)),
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
