EIP170_LIMIT = 24_576

EXPECTED_DEPLOYED_RUNTIME_BYTES = {
    "MissionControl": 16_064,
    "SwitchboardBravo": 23_082,
    # VaultMigrator centralizes all three migration paths. Adding its canonical
    # ID/getters to Addys also changes the runtime of Addys consumers.
    "SwitchboardEcho": 23_053,
    "VaultMigrator": 12_042,
    "Teller": 24_525,
    "TellerUtils": 8_976,
    "Ledger": 13_306,
    "Lootbox": 22_993,
    "CreditEngine": 24_392,
    "StabilityPool": 24_371,
}

# The owner accepted Teller's current 24,525-byte deployed runtime during this
# migration review. Keep both the exact-size assertion above and its remaining
# 51-byte margin as hard gates: any further growth requires a new disposition.
MIN_TELLER_MARGIN = 51
MIN_LOOTBOX_MARGIN = 20


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
    human_resources,
    credit_engine,
    credit_redeem,
    stability_pool,
):
    deployed_runtime_bytes = {
        "MissionControl": len(mission_control.env.get_code(mission_control.address)),
        "SwitchboardAlpha": len(switchboard_alpha.env.get_code(switchboard_alpha.address)),
        "SwitchboardBravo": len(switchboard_bravo.env.get_code(switchboard_bravo.address)),
        "SwitchboardCharlie": len(switchboard_charlie.env.get_code(switchboard_charlie.address)),
        "SwitchboardEcho": len(switchboard_echo.env.get_code(switchboard_echo.address)),
        "VaultMigrator": len(vault_migrator.env.get_code(vault_migrator.address)),
        "Teller": len(teller.env.get_code(teller.address)),
        "TellerUtils": len(teller_utils.env.get_code(teller_utils.address)),
        "BondRoom": len(bond_room.env.get_code(bond_room.address)),
        "Ledger": len(ledger.env.get_code(ledger.address)),
        "Lootbox": len(lootbox.env.get_code(lootbox.address)),
        "HumanResources": len(human_resources.env.get_code(human_resources.address)),
        "CreditEngine": len(credit_engine.env.get_code(credit_engine.address)),
        "CreditRedeem": len(credit_redeem.env.get_code(credit_redeem.address)),
        "StabilityPool": len(stability_pool.env.get_code(stability_pool.address)),
    }
    print("DEPLOYED_RUNTIME_BYTES", deployed_runtime_bytes)

    assert {
        name: deployed_runtime_bytes[name]
        for name in EXPECTED_DEPLOYED_RUNTIME_BYTES
    } == EXPECTED_DEPLOYED_RUNTIME_BYTES

    oversized = {
        name: size
        for name, size in deployed_runtime_bytes.items()
        if size > EIP170_LIMIT
    }
    assert not oversized, f"EIP-170 runtime limit exceeded: {oversized}"

    teller_margin = EIP170_LIMIT - deployed_runtime_bytes["Teller"]
    assert teller_margin >= MIN_TELLER_MARGIN, (
        f"Teller deployed margin {teller_margin} is below the {MIN_TELLER_MARGIN}-byte floor"
    )

    # Normal claims now own all post-migration reward and registration cleanup; removing
    # the eager settlement path recovered material headroom. Keep the existing branch
    # floor as an independent lower bound; exact deployed sizes above still make every
    # future byte change explicit.
    lootbox_margin = EIP170_LIMIT - deployed_runtime_bytes["Lootbox"]
    assert lootbox_margin >= MIN_LOOTBOX_MARGIN, (
        f"Lootbox deployed margin {lootbox_margin} is below the {MIN_LOOTBOX_MARGIN}-byte floor"
    )
