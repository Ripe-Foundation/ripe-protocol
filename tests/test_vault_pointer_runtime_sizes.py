EIP170_LIMIT = 24_576

EXPECTED_DEPLOYED_RUNTIME_BYTES = {
    "MissionControl": 15_998,
    "SwitchboardBravo": 23_082,
    # deposit-vault position migration pinned every contract it changed
    "SwitchboardEcho": 22_912,
    "Teller": 24_258,
    "TellerUtils": 11_900,
    "Ledger": 13_306,
    "Lootbox": 22_665,
    "CreditEngine": 24_392,
    "StabilityPool": 24_371,
}

# Teller carries the tightest budget of any contract here: the migration work left
# 24_576 - 24_258 = 318 bytes of headroom. Treat any further Teller growth as gated.
#
# This floor was reconciled by the owner on 2026-08-07. Two floors had been written
# down independently: 200 bytes in the deposit-vault hardening plan
# (docs/chains/rh/deposit-vault-smart-contract-hardening-implementation-plan.md
# section 5.3, "RG-SIZE-01"), and 300 here, set by the vault-migration work. They
# disagreed on the same proposed change -- the Section 13 Teller receipt-window
# guard measures +81 bytes, landing at 237 bytes of headroom, which passes 200 and
# fails 300. The owner ruled that the hardening plan's 200 governs, so this is
# lowered to match rather than leaving two contradictory rules in the tree.
#
# Lowering it is a deliberate relaxation of a guard the migration workstream set.
# The 318 bytes currently present still clear the old 300 as well; nothing about
# the deployed contract changed.
MIN_TELLER_MARGIN = 200


def test_pointer_changed_contracts_fit_eip170_deployed_runtime_limit(
    mission_control,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    switchboard_echo,
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
