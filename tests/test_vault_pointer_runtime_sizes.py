import hashlib
from pathlib import Path
import re

import boa
import pytest
import yaml


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
    # The base artifact ledger measured 23,345 bytes even though this explicitly
    # non-enforced review aid still said 22,993. The initial SC-15 implementation
    # added 67 bytes; preserving zero-asset Ledger registrations recovers 49,
    # producing a final 23,363 (352 bytes of pre-existing reference drift plus
    # 18 bytes of growth owned by this batch).
    "Lootbox": 23_363,
    "RipeGov": 23_152,
    "AuctionHouse": 24_554,
    "CreditEngine": 24_555,
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
# AuctionHouse 22, Teller 20, CreditEngine 21, StabilityPool 263,
# SwitchboardCharlie 703,
# SwitchboardAlpha 108, Lootbox 1,213, RipeGov 1,424, SwitchboardBravo 373,
# SwitchboardEcho 1,384, and the rest far larger.
#
# RH-D029 covered the prior exact CreditEngine artifact and reopened with this
# source change. RH-D037 replaces it for the exact 21-byte-headroom SC-11/SC-15
# artifact and permits zero further growth. RH-D030 separately waives the exact
# 108-byte-headroom SwitchboardAlpha artifact; RH-D032 covers the exact
# 20-byte-headroom Teller artifact, and RH-D036 covers AuctionHouse.
#
MIN_HEADROOM_OVERRIDES = {
    "AuctionHouse": 22,  # RH-D036; exact conservation artifact, zero growth
    "CreditEngine": 21,  # RH-D037; exact SC-11/SC-15 artifact, zero growth
    "SwitchboardAlpha": 108,  # RH-D030; exact priority-vault validation artifact
    "Teller": 20,  # RH-D032; exact minimum-payout artifact, zero growth
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
    "AuctionHouse": {
        "decision": "RH-D036",
        "fixture": "auction_house",
        "source": "contracts/core/AuctionHouse.vy",
        "source_sha256": (
            "e7eb7b1b80ae0dce6a9df21ad7ec35cc3fd2248aac0bc3f02797d99b10e8409e"
        ),
        "runtime_sha256": (
            "0405767ec38653c4f50257add6ceb072751761550337f711d99465274901bcb2"
        ),
        "runtime_template_bytes": 24_458,
        "deployed_runtime_bytes": 24_554,
        "pinned_hq": "0x00000000000000000000000000000000000000A4",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A4",
        ),
        "deployed_sha256": (
            "d6cb1d92c9e08126e7191b1f701617954af196353ef03b532079c645de9320a6"
        ),
    },
    "CreditEngine": {
        "decision": "RH-D037",
        "fixture": "credit_engine",
        "source": "contracts/core/CreditEngine.vy",
        "source_sha256": (
            "506efeaa9e6c4ac16b5462b044ce3c0033099fbdc1f608a1e76c945b85bb48cb"
        ),
        "runtime_sha256": (
            "2897887d02772092a9211cb548bcc05d310f700cfca54f0abb08192588340d6e"
        ),
        "runtime_template_bytes": 24_459,
        "deployed_runtime_bytes": 24_555,
        "pinned_hq": "0x00000000000000000000000000000000000000A1",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A1",
        ),
        "deployed_sha256": (
            "fad9a048b57869a34844508914675e4fbd0e5107e3767e8e17c324e59b7fc759"
        ),
    },
    "SwitchboardAlpha": {
        "decision": "RH-D030",
        "fixture": "switchboard_alpha",
        "source": "contracts/config/SwitchboardAlpha.vy",
        "source_sha256": (
            "51aab6ff276c9fe85f323899356f6bf7e722782cd969e30d3719612677fa24d5"
        ),
        "runtime_sha256": (
            "eec69265f4cfa7157bcf97b16ab05ec8cd3721a04d2659ea0d25bf16f5dce7c9"
        ),
        "runtime_template_bytes": 24_244,
        "deployed_runtime_bytes": 24_468,
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
            "475d777c48ab2671e6f19967db1ebb8304de590a3e71413da2fec84acff59055"
        ),
    },
    "Teller": {
        "decision": "RH-D032",
        "fixture": "teller",
        "source": "contracts/core/Teller.vy",
        "source_sha256": (
            "1ac2fd7b2c36fe454fd4fcdc0b422237f6a4936c5128bccada16524301a6b049"
        ),
        "runtime_sha256": (
            "9fd5e961f9f94593694b9fc0cef33ea5ec875e837132c34eeda8b14c0360e1c1"
        ),
        "runtime_template_bytes": 24_460,
        "deployed_runtime_bytes": 24_556,
        "pinned_hq": "0x00000000000000000000000000000000000000A2",
        "constructor_args": (
            "0x00000000000000000000000000000000000000A2",
            False,
        ),
        "deployed_sha256": (
            "ea228bd7c41c3b1cc60dcbc29fde55c1fa21718b67aea6dcb0afc30e5da6daa3"
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
    auction_house,
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
        "AuctionHouse": len(auction_house.env.get_code(auction_house.address)),
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


def test_rh_decision_register_status_and_waiver_ids_have_exact_parity():
    register_text = (ROOT / "docs/chains/rh/decision-register.md").read_text()
    register_rows = re.findall(
        r"^### (RH-D\d{3}) — (.+)$",
        register_text,
        flags=re.MULTILINE,
    )
    register = dict(register_rows)
    assert len(register) == len(register_rows), "duplicate RH decision ID"

    status = yaml.safe_load((ROOT / "docs/chains/rh/status.yaml").read_text())
    status_rows = [
        (row["id"], row["title"])
        for row in status["decisions"]
        if row["id"].startswith("RH-D")
    ]
    status_decisions = dict(status_rows)
    assert len(status_decisions) == len(status_rows), "duplicate status RH decision ID"
    fully_retired = {
        row["id"]
        for row in status["decisions"]
        if row["id"].startswith("RH-D")
        and row["status"] == "retired_default_floor_restored"
    }
    assert fully_retired == {"RH-D026"}
    assert status["counts"]["rh_d_decisions"] == (
        len(status_rows) - len(fully_retired)
    )
    assert status_decisions == register

    waiver_decisions = {
        pinned["decision"] for pinned in WAIVED_CONTRACT_IDENTITIES.values()
    }
    assert waiver_decisions <= set(register)


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
