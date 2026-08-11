"""DRAFT — owner approval required before integration or use."""

import json

import pytest

from scripts.proposals import lootbox_deployment_profiles as profiles


@pytest.fixture(scope="module")
def manifest():
    return profiles.load_manifest()


@pytest.fixture(scope="module")
def compiled():
    return profiles.compile_reviewed_lootbox()


def test_r5_manifest_is_canonical_draft_and_path_free(manifest):
    profiles.validate_manifest(manifest)
    raw = profiles.MANIFEST_PATH.read_bytes()
    assert raw == profiles.shared.canonical_json_bytes(manifest)
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    assert b"/Users/" not in raw
    assert b"timestamp" not in raw.lower()

    expected = json.loads(profiles.EXPECTATIONS_PATH.read_text())["contracts"][
        "Lootbox"
    ]
    assert manifest["source"] == {
        "compiler_settings": expected["compiler_settings"],
        "effective_optimization": expected["effective_optimization"],
        "path": "contracts/core/Lootbox.vy",
        "sha256": expected["source_sha256"],
        "transitive_compiler_input_integrity": expected[
            "transitive_compiler_input_integrity"
        ],
        "vyper_version": profiles.PINNED_VYPER_VERSION,
    }


def test_r5_placeholders_are_deterministic_and_unapproved(manifest):
    ripe_hq = manifest["shared_inputs"]["ripe_hq"]
    assert ripe_hq["value"] == profiles.shared.deterministic_placeholder_address(
        ripe_hq["label"]
    )
    assert ripe_hq["approval_status"] == "unapproved_placeholder"

    enabled = manifest["postures"]["base_preserving_enabled"]["inputs"]
    assert enabled["deposit_rewards_amount"]["value"] == (
        profiles.deterministic_placeholder_amount(
            "base-lootbox-profile:deposit-rewards"
        )
    )
    assert enabled["yield_bonus_amount"]["value"] == (
        profiles.deterministic_placeholder_amount(
            "base-lootbox-profile:yield-bonus"
        )
    )
    assert enabled["deposit_rewards_amount"]["approval_status"] == (
        "unapproved_placeholder"
    )
    assert enabled["yield_bonus_amount"]["approval_status"] == (
        "unapproved_placeholder"
    )


def test_r5_compiles_reviewed_lootbox_with_source_owned_codesize(compiled):
    assert len(compiled.creation) == 23_207
    assert len(compiled.runtime_template) == 22_865
    assert compiled.integrity == (
        "8328a99cf69a6d5c8d6f9e575737057c"
        "fbaddc3d15fe0f8d1554be1a5e37320f"
    )


@pytest.mark.parametrize("posture", sorted(profiles.POSTURE_RULES))
def test_r5_each_posture_deploys_and_completes_constructor_readbacks(
    posture,
    manifest,
    compiled,
):
    deployment = profiles.deploy_local_posture(
        posture,
        manifest=manifest,
        compiled=compiled,
    )
    assert deployment.arguments == profiles.ordered_arguments(
        manifest,
        posture,
    )
    assert deployment.evidence == {
        key: True for key in profiles.REQUIRED_EVIDENCE
    }


def test_x1_current_constructor_abi_maps_exactly_to_manifest_order(manifest):
    abi = json.loads((profiles.ROOT / "scripts/abis/Lootbox.json").read_text())
    constructors = [entry for entry in abi if entry["type"] == "constructor"]
    assert len(constructors) == 1
    actual = [
        (entry["name"], entry["type"])
        for entry in constructors[0]["inputs"]
    ]
    assert actual == [
        ("_ripeHq", "address"),
        ("_minUnderscoreSendInterval", "uint256"),
        ("_underscoreSendInterval", "uint256"),
        ("_undyDepositRewardsAmount", "uint256"),
        ("_undyYieldBonusAmount", "uint256"),
    ]
    assert manifest["constructor_order"] == list(profiles.CONSTRUCTOR_ORDER)

    for posture in profiles.POSTURE_RULES:
        arguments = profiles.ordered_arguments(manifest, posture)
        assert len(arguments) == len(actual) == 5
        assert arguments[0] == manifest["shared_inputs"]["ripe_hq"]["value"]
        for index, schema_name in enumerate(
            manifest["constructor_order"][1:],
            start=1,
        ):
            assert arguments[index] == (
                manifest["postures"][posture]["inputs"][schema_name]["value"]
            )


def _historical_lootbox_constructor_arities(path):
    import ast

    tree = ast.parse(path.read_text())
    arities = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "deploy"
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "Lootbox"
        ):
            continue
        arities.append(len(node.args) - 1)
    return arities


@pytest.mark.parametrize(
    ("relative", "sha256", "historical_arity"),
    [
        (
            "migrations/base-mainnet/1016_Lootbox.py",
            "fce8645fe23f65085ffe8b6b0c6098a857c298f14f3185b84331577c02f2a0c0",
            1,
        ),
        (
            "migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py",
            "3665b0334902a764b9d51c29022c2b99701f51d301c3034e8738164149c9b893",
            1,
        ),
        (
            "migrations/base-mainnet/2025080900_Lootbox.py",
            "f98b8884a35a412503d43ef8772197fd8e2c05415e8806773ae5cf9aebb9260a",
            1,
        ),
        (
            "migrations/base-mainnet/2025112500_New_Endaoment_Features.py",
            "bdbe2ae2749da6c42b0a347034515544cfb5b60498a6180af66c38960155edb1",
            4,
        ),
    ],
)
def test_x1_historical_base_call_site_is_pinned_and_current_arity_incompatible(
    relative,
    sha256,
    historical_arity,
):
    import hashlib

    path = profiles.ROOT / relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha256
    assert _historical_lootbox_constructor_arities(path) == [
        historical_arity
    ]
    assert historical_arity != len(profiles.CONSTRUCTOR_ORDER) == 5


def test_x1_historical_call_site_inventory_is_complete():
    discovered = {}
    for root_name in ("migrations", "migration_history"):
        root = profiles.ROOT / root_name
        for path in sorted(root.rglob("*.py")):
            arities = _historical_lootbox_constructor_arities(path)
            if arities:
                discovered[path.relative_to(profiles.ROOT).as_posix()] = (
                    arities
                )

    assert discovered == {
        "migrations/base-mainnet/1016_Lootbox.py": [1],
        "migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py": [1],
        "migrations/base-mainnet/2025080900_Lootbox.py": [1],
        "migrations/base-mainnet/2025112500_New_Endaoment_Features.py": [4],
        "migrations/robinhood-mainnet/0005_Departments.py": [5],
    }
