EIP170_LIMIT = 24_576

# Reference sizes recorded by the deposit-vault position migration. These are a
# review aid only; nothing asserts equality against them, because they go stale
# whenever a contract legitimately changes. What is enforced is the EIP-170
# ceiling and the headroom floors below.
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

# Minimum EIP-170 headroom every contract in this set must keep.
#
# The EIP-170 ceiling alone is not a sufficient guard: a contract may consume all
# of its remaining headroom and still sit one byte under the limit, leaving no
# room for the next change and no warning that it happened. This floor fails
# while there is still margin to react.
#
# Measured headroom at the time of writing, against the 24,576 limit:
#   CreditEngine 184, StabilityPool 205, Teller 329, SwitchboardCharlie 1,091,
#   SwitchboardAlpha 1,142, SwitchboardBravo 1,494, SwitchboardEcho 1,664,
#   Lootbox 2,453, and the rest far larger.
#
# CreditEngine and StabilityPool are already tighter than Teller. The default is
# set below their current headroom so this does not fail on arrival, while still
# catching a contract that eats what it has left.
DEFAULT_MIN_HEADROOM = 150

# Per-contract overrides. Teller's 200 is owner-ratified (RG-SIZE-01, reconciled
# 2026-08-08); see docs/chains/rh/deposit-vault-hardening-wp0-evidence.md section
# 1. Do not lower it without the same owner decision that set it.
MIN_HEADROOM_OVERRIDES = {
    "Teller": 200,
}

# Teller's floor was reconciled by the owner on 2026-08-08, resolving RG-SIZE-01.
# The disposition is recorded in docs/chains/rh/deposit-vault-hardening-wp0-evidence.md
# (section 1, "RG-SIZE-01 disposition"; it also closes finding E-8 there) -- update
# both together if it is ever revisited.
#
# Two floors had been written down independently: 200 bytes in the deposit-vault
# hardening plan (docs/chains/rh/deposit-vault-smart-contract-hardening-implementation-plan.md
# section 5.3, "RG-SIZE-01"), and 300 here, set by the vault-migration work. They
# disagreed on the same proposed change -- the Section 13 Teller receipt-window
# guard measures +81 bytes, landing at 237 bytes of headroom, which passes 200 and
# fails 300. The owner ruled that the hardening plan's 200 governs.
#
# The plan's other half is unchanged and still binding: anything landing *below*
# 200 bytes needs a separate exact owner waiver (e.g. M9 at 127 bytes).
MIN_TELLER_MARGIN = MIN_HEADROOM_OVERRIDES["Teller"]


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

    # No exact-size equality against EXPECTED_DEPLOYED_RUNTIME_BYTES.
    #
    # An earlier revision of this comment blamed those stale numbers on a
    # macOS-arm64 versus Linux-x86_64 difference. That was wrong, and the
    # correction matters because the wrong explanation invites the wrong fix.
    # The sizes are deterministic for a given source: a Linux Actions runner and
    # a local macOS arm64 run produce identical values on the same tree. What had
    # actually happened is that rh commit 3a5f840 changed Teller, Ledger, and
    # Lootbox, so the pinned dict was measuring an older source. The comparison
    # that produced the false conclusion was local head against a CI run of the
    # pull_request *merge* ref, which already contained those newer contracts.
    #
    # Equality is still not the right assertion — it fails on any legitimate
    # change, in either direction, and says nothing about safety. What is
    # enforced instead is the property that actually protects a deployment:
    # nothing exceeds EIP-170, and every contract keeps usable headroom.

    oversized = {
        name: size
        for name, size in deployed_runtime_bytes.items()
        if size > EIP170_LIMIT
    }
    assert not oversized, f"EIP-170 runtime limit exceeded: {oversized}"

    headroom = {
        name: EIP170_LIMIT - size for name, size in deployed_runtime_bytes.items()
    }
    tight = {
        name: margin
        for name, margin in headroom.items()
        if margin < MIN_HEADROOM_OVERRIDES.get(name, DEFAULT_MIN_HEADROOM)
    }
    assert not tight, (
        "EIP-170 headroom floor breached: "
        + ", ".join(
            f"{name} has {margin} bytes, floor is "
            f"{MIN_HEADROOM_OVERRIDES.get(name, DEFAULT_MIN_HEADROOM)}"
            for name, margin in sorted(tight.items())
        )
    )
