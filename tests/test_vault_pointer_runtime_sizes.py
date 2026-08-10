import hashlib
from pathlib import Path

import boa
import pytest


ROOT = Path(__file__).resolve().parents[1]

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
# 200 is the ratified rule, not a number chosen here. The deposit-vault hardening
# plan section 11.5 sets "at least 200 bytes of headroom" as the acceptance
# threshold for a changed deployed contract, and its stop-condition list repeats
# that anything below 200 requires an exact owner waiver under RG-SIZE-01.
#
# An earlier revision of this file set the default to 150. That silently lowered
# a ratified rule for every contract, and a review caught it: a synthetic
# StabilityPool at 176 bytes of headroom violated the recorded rule and still
# passed. The default is now the ratified value.
DEFAULT_MIN_HEADROOM = 200

# Measured headroom against the 24,576 limit at the time of writing:
#   CreditEngine 184, StabilityPool 205, Teller 329, SwitchboardCharlie 1,091,
#   SwitchboardAlpha 1,142, SwitchboardBravo 1,494, SwitchboardEcho 1,664,
#   Lootbox 2,453, and the rest far larger.
#
# CreditEngine sits at 184, below the ratified 200. That position is inherited
# from rh — this branch changes no production contract — and it is carried here
# as an explicit, dated owner waiver rather than by weakening the rule for
# everything. See RH-D026 in docs/chains/rh/decision-register.md for the scope,
# rationale, and reconsideration trigger.
#
# Teller's 200 is the ratified value reconciled on 2026-08-08 (RG-SIZE-01); see
# docs/chains/rh/deposit-vault-hardening-wp0-evidence.md section 1. It is stated
# explicitly rather than inherited from the default so that changing the default
# cannot silently move it.
MIN_HEADROOM_OVERRIDES = {
    "Teller": 200,
    "CreditEngine": 184,  # RH-D026 waiver; do not lower without a new decision
}

# Exact identity of every contract carrying a below-floor waiver.
#
# A headroom floor is the wrong instrument on its own for a waived contract, and
# a review demonstrated why. RH-D026 promises the waiver is withdrawn when
# CreditEngine is next changed, but the floor only observes a byte count. The
# reviewer changed a real production rule --
#
#     assert _discount <= HUNDRED_PERCENT   ->   assert _discount < HUNDRED_PERCENT
#
# which makes a 100% discount invalid, and the deployed runtime stayed at exactly
# 24,392 bytes. The floor passed. The waived contract had changed behaviour and
# the decision that waived it never reopened.
#
# So while a contract is below DEFAULT_MIN_HEADROOM it is pinned to the exact
# artifact the owner waived, not merely to a size:
#
#   source_sha256   -- sha256 of the .vy source bytes. Compiler-independent, and
#                      the check that catches the same-size semantic edit above.
#   runtime_sha256  -- sha256 of the immutable-free runtime template
#                      (`compiler_data.bytecode_runtime`). Catches a change in
#                      what the compiler emits from unchanged source.
#   deployed_runtime_bytes -- exact deployed size, immutables included. Pinned
#                      rather than floored, so growth *and* shrinkage are visible.
#   pinned_hq / deployed_sha256 -- sha256 of the *complete deployed runtime*,
#                      immutables included, for one declared constructor input.
#
# On that last pair, and on what "exact artifact" can honestly mean here. A
# review showed the first four identities do not pin the deployed byte string:
# deploying CreditEngine with a different `RIPE_HQ_FOR_ADDYS` changes the
# deployed bytes -- including the registry authority the contract trusts -- while
# the length stays at exactly 24,392, so every check above still passed. The
# claim that this waiver covered "one exact artifact" was therefore false as
# written.
#
# It is closed by deploying the contract here with a *declared* HQ constant and
# hashing the result, which is fully deterministic and independent of whatever
# the session fixture happens to wire up. `pinned_hq` is not a real address and
# is not expected to be one; it exists only to make the immutable input fixed so
# the deployed bytes are reproducible.
#
# What remains deliberately unbound is the immutable input of any *particular*
# deployment. Constructor arguments are deployment configuration, not contract
# version: a fixture or a chain wiring a different HQ produces different deployed
# bytes without changing a line of CreditEngine. Binding those would make a code
# *size* waiver fail on test-infrastructure changes that cannot affect code size.
# The deployed size of the real fixture deployment is still checked exactly.
#
# Any of the three moving fails this test, and the required response is a new
# owner decision at the new figure -- not an edit to these constants. Refreshing
# a hash to make this green is the exact move it exists to prevent.
#
# This binding is exceptional and self-retiring: it applies only while a contract
# sits below the ratified floor. When CreditEngine returns to 200+ bytes of
# headroom, its MIN_HEADROOM_OVERRIDES entry and this entry are both removed, and
# it goes back to being governed by the floor like everything else.
WAIVED_CONTRACT_IDENTITIES = {
    "CreditEngine": {
        "decision": "RH-D026",
        "fixture": "credit_engine",
        "source": "contracts/core/CreditEngine.vy",
        "source_sha256": (
            "d8fae4e9cffff0d95adbe48a59e57c622585f021017b94089f8a70e615c36e43"
        ),
        "runtime_sha256": (
            "e75de103fc42b14907ddc409e55cc1366a82c6c8f9cf0719dd3dbe197610b943"
        ),
        "runtime_template_bytes": 24_296,
        "deployed_runtime_bytes": 24_392,
        # Declared constructor input, so the deployed bytes below are fixed.
        # Not a real HQ and not required to be one.
        "pinned_hq": "0x00000000000000000000000000000000000000A1",
        "deployed_sha256": (
            "12a781ca7793d79a866c3285f67f80fce65342dffc86239054a00653e94f7ac5"
        ),
    },
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


def test_every_below_floor_waiver_declares_an_exact_identity():
    # The two tables cannot drift apart. Granting a new sub-floor override without
    # pinning the artifact it waives would recreate exactly the gap RH-D026 had:
    # a promise to reopen on the next change, enforced by a check that cannot see
    # a change. Removing an override without removing its identity entry is the
    # same mistake pointed the other way -- the contract is back above the floor
    # and no longer needs the exceptional binding.
    waived = {
        name
        for name, floor in MIN_HEADROOM_OVERRIDES.items()
        if floor < DEFAULT_MIN_HEADROOM
    }
    assert waived == set(WAIVED_CONTRACT_IDENTITIES), (
        "below-floor waivers and pinned identities disagree: "
        f"waived={sorted(waived)}, pinned={sorted(WAIVED_CONTRACT_IDENTITIES)}"
    )

    for name, pinned in WAIVED_CONTRACT_IDENTITIES.items():
        floor = MIN_HEADROOM_OVERRIDES[name]
        assert EIP170_LIMIT - pinned["deployed_runtime_bytes"] == floor, (
            f"{name}: pinned deployed size implies "
            f"{EIP170_LIMIT - pinned['deployed_runtime_bytes']} bytes of headroom, "
            f"but its recorded floor is {floor}"
        )


@pytest.mark.parametrize("name", sorted(WAIVED_CONTRACT_IDENTITIES))
def test_waived_contract_is_exactly_the_artifact_the_owner_waived(name, request):
    pinned = WAIVED_CONTRACT_IDENTITIES[name]
    decision = pinned["decision"]
    reopen = (
        f"\n\n{name} is below the ratified {DEFAULT_MIN_HEADROOM}-byte floor under "
        f"{decision}, which waives one exact artifact. This contract is no longer "
        f"that artifact, so the waiver does not cover it. Withdraw {decision} and "
        "record a new owner decision at the new figure. Do not refresh the "
        "constants in this file to make this pass."
    )

    source_path = ROOT / pinned["source"]
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert source_sha == pinned["source_sha256"], (
        f"{pinned['source']} changed: sha256 is {source_sha}, "
        f"{decision} waived {pinned['source_sha256']}." + reopen
    )

    # Immutable-free runtime template: identical for a given source and compiler,
    # and independent of whatever constructor arguments a fixture happens to use.
    runtime_template = boa.load_partial(
        str(source_path)
    ).compiler_data.bytecode_runtime
    assert len(runtime_template) == pinned["runtime_template_bytes"], (
        f"{name} runtime template is {len(runtime_template)} bytes, "
        f"{decision} waived {pinned['runtime_template_bytes']}." + reopen
    )
    runtime_sha = hashlib.sha256(runtime_template).hexdigest()
    assert runtime_sha == pinned["runtime_sha256"], (
        f"{name} runtime template sha256 is {runtime_sha}, {decision} waived "
        f"{pinned['runtime_sha256']}. The source is unchanged, so this is a "
        "compiler-output change." + reopen
    )

    contract = request.getfixturevalue(pinned["fixture"])
    deployed = len(contract.env.get_code(contract.address))
    assert deployed == pinned["deployed_runtime_bytes"], (
        f"{name} deploys {deployed} bytes, {decision} waived exactly "
        f"{pinned['deployed_runtime_bytes']} "
        f"({EIP170_LIMIT - deployed} bytes of headroom, not "
        f"{EIP170_LIMIT - pinned['deployed_runtime_bytes']})." + reopen
    )

    # The complete deployed byte string, immutables included, for the declared
    # constructor input. The four checks above all pass when only an immutable
    # changes -- a review demonstrated that -- so without this the waiver does
    # not bind what it says it binds.
    fixed = boa.load(
        str(source_path), pinned["pinned_hq"], name=f"{name.lower()}_waiver_identity"
    )
    fixed_code = fixed.env.get_code(fixed.address)
    assert len(fixed_code) == pinned["deployed_runtime_bytes"], (
        f"{name} at the declared HQ deploys {len(fixed_code)} bytes, "
        f"{decision} waived {pinned['deployed_runtime_bytes']}." + reopen
    )
    fixed_sha = hashlib.sha256(fixed_code).hexdigest()
    assert fixed_sha == pinned["deployed_sha256"], (
        f"{name} deployed at HQ {pinned['pinned_hq']} hashes to {fixed_sha}, "
        f"{decision} waived {pinned['deployed_sha256']}. Same size, different "
        "bytes: this is a change the size checks above cannot see." + reopen
    )
