import hashlib
from pathlib import Path

import boa
import pytest


ROOT = Path(__file__).resolve().parents[1]

EIP170_LIMIT = 24_576

# Reference sizes recorded by the deposit-vault position migration and refreshed
# when one of these contracts is explicitly changed. These are a review aid only;
# nothing asserts equality against them. What is enforced is the EIP-170 ceiling
# and the headroom floors below.
EXPECTED_DEPLOYED_RUNTIME_BYTES = {
    "MissionControl": 16_064,
    "SwitchboardBravo": 23_082,
    # VaultMigrator centralizes all three migration paths. Adding its canonical
    # ID/getters to Addys also changes the runtime of Addys consumers.
    "SwitchboardEcho": 23_104,
    "VaultMigrator": 12_042,
    "Teller": 24_556,
    "TellerUtils": 8_976,
    "Ledger": 13_306,
    "Lootbox": 22_993,
    "RipeGov": 23_572,
    "CreditEngine": 24_566,
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

# Measured headroom against the 24,576 limit in this integration candidate:
# Teller 20, CreditEngine 10, StabilityPool 263, SwitchboardCharlie 703,
# SwitchboardAlpha 2, Lootbox 1,231, RipeGov 1,004, SwitchboardBravo 373,
# SwitchboardEcho 1,384, and the rest far larger.
#
# CreditEngine reopened and retired RH-D026 when this source changed. The owner
# granted replacement RH-D029 for this exact 10-byte-headroom combined
# reward-suppression, payer-refund, and redemption-isolation artifact. RH-D030
# separately waives the exact 2-byte-headroom SwitchboardAlpha artifact, and
# RH-D031 waives the exact 20-byte-headroom Teller third-party-touch artifact.
# See the decision register.
#
MIN_HEADROOM_OVERRIDES = {
    "CreditEngine": 10,  # RH-D029; exact combined artifact, zero growth
    "SwitchboardAlpha": 2,  # RH-D030; exact debt-config and priority-vault artifact
    "Teller": 20,  # RH-D031; exact third-party-touch artifact, zero growth
}

# Preserve the migration branch's explicit contract-specific guards. Lootbox is
# also covered by the stronger 200-byte default; RipeGov deliberately keeps its
# independently accepted 1,000-byte minimum.
MIN_LOOTBOX_MARGIN = 20
MIN_RIPE_GOV_MARGIN = 1_000

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
# Any identity moving fails this test, and the required response is a new
# owner decision at the new figure -- not an edit to these constants. Refreshing
# a hash to make this green is the exact move it exists to prevent.
#
# This binding is exceptional and self-retiring: it applies only while a contract
# sits below the ratified floor. When a waived contract returns to 200+ bytes of
# headroom, its override and identity entry are both removed, and it goes back to
# being governed by the floor like everything else.
WAIVED_CONTRACT_IDENTITIES = {
    "CreditEngine": {
        "decision": "RH-D029",
        "fixture": "credit_engine",
        "source": "contracts/core/CreditEngine.vy",
        "source_sha256": (
            "98001bce0f07992bdc51e4dede81fce5fbccbdaf9862c3ecef7694f6a2bd4f3f"
        ),
        "runtime_sha256": (
            "0cf18bd4121836b960abff777f3bca468c7fbaaad7b18e5601c9d5e5af870d91"
        ),
        "runtime_template_bytes": 24_470,
        "deployed_runtime_bytes": 24_566,
        "pinned_hq": "0x00000000000000000000000000000000000000A1",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A1",
        ),
        "deployed_sha256": (
            "4f410105098b45e93a418afbbc6f49b4154528cdc8253543f37b271b6ba03820"
        ),
    },
    "SwitchboardAlpha": {
        "decision": "RH-D030",
        "fixture": "switchboard_alpha",
        "source": "contracts/config/SwitchboardAlpha.vy",
        "source_sha256": (
            "a967459ca6711cb67f66af6bbdb8c7a7af517a1587b7ca0aa5146ad318efcfa9"
        ),
        "runtime_sha256": (
            "e378970cbf4ea05049dfcb45e2d542f05720fddfd133482418c47590afe7f4b0"
        ),
        "runtime_template_bytes": 24_350,
        "deployed_runtime_bytes": 24_574,
        "pinned_hq": "0x00000000000000000000000000000000000000A1",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A1",
            "0x00000000000000000000000000000000000000A2",
            1,
            2,
            1,
            2,
        ),
        "deployed_sha256": (
            "32787aab311b5535e57492437a0c51e31f8c5226f8c205dc953d6111c05ba6c4"
        ),
    },
    "Teller": {
        "decision": "RH-D031",
        "fixture": "teller",
        "source": "contracts/core/Teller.vy",
        "source_sha256": (
            "5cb7d059299cacfde30a3e45ee860a6f150bc7f37d361d363f946a662e9945ac"
        ),
        "runtime_sha256": (
            "2bc9b992027b3432dc16c0e2d33f7a1df83df3f863b46dac8ff610e155e10859"
        ),
        "runtime_template_bytes": 24_460,
        "deployed_runtime_bytes": 24_556,
        "pinned_hq": "0x00000000000000000000000000000000000000A2",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A2",
            False,
        ),
        "deployed_sha256": (
            "6afe50f0f67f0a8c5ae7319ae12d02b280259b78ed29a615578777be7c0fc7a2"
        ),
    },
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
    ripe_gov_vault,
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
        "RipeGov": len(ripe_gov_vault.env.get_code(ripe_gov_vault.address)),
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

    lootbox_margin = EIP170_LIMIT - deployed_runtime_bytes["Lootbox"]
    assert lootbox_margin >= MIN_LOOTBOX_MARGIN, (
        f"Lootbox deployed margin {lootbox_margin} is below the "
        f"{MIN_LOOTBOX_MARGIN}-byte floor"
    )

    ripe_gov_margin = EIP170_LIMIT - deployed_runtime_bytes["RipeGov"]
    assert ripe_gov_margin >= MIN_RIPE_GOV_MARGIN, (
        f"RipeGov deployed margin {ripe_gov_margin} is below the "
        f"{MIN_RIPE_GOV_MARGIN}-byte floor"
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
        assert pinned["constructor_args"][0] == pinned["pinned_hq"], (
            f"{name}: declared HQ and fixed constructor arguments disagree"
        )
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
    if name == "SwitchboardAlpha":
        # LocalGov resolves three immutable inputs from RipeHq during
        # construction. Bind those reads to deterministic values so the waiver
        # covers the complete deployed byte string, not only its length.
        boa.loads(
            """
# pragma version 0.4.3

@view
@external
def governance() -> address:
    return 0x00000000000000000000000000000000000000A3

@view
@external
def minGovChangeTimeLock() -> uint256:
    return 1

@view
@external
def maxGovChangeTimeLock() -> uint256:
    return 2
""",
            name="switchboard_alpha_waiver_hq",
            override_address=pinned["pinned_hq"],
        )

    fixed = boa.load(
        str(source_path),
        *pinned["constructor_args"],
        name=f"{name.lower()}_waiver_identity",
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
