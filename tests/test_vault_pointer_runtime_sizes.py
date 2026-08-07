EIP170_LIMIT = 24_576

EXPECTED_DEPLOYED_RUNTIME_BYTES = {
    "MissionControl": 15_998,
    "SwitchboardBravo": 23_082,
    "Teller": 24_139,
    "CreditEngine": 24_392,
    "StabilityPool": 24_371,
}


def test_pointer_changed_contracts_fit_eip170_deployed_runtime_limit(
    mission_control,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    teller,
    bond_room,
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
        "Teller": len(teller.env.get_code(teller.address)),
        "BondRoom": len(bond_room.env.get_code(bond_room.address)),
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
