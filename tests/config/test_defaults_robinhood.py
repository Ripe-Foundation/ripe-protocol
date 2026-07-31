"""H-04 canonical Robinhood manifest and fail-closed generator tests."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPOSITORY / "scripts/params/generate_robinhood_defaults.py"
MANIFEST_PATH = REPOSITORY / "config/robinhood-parameters.json"
REAL_OUTPUT = REPOSITORY / "contracts/config/DefaultsRobinhood.vy"
EXPECTED_GENERATION_BLOCKERS = (
    "Defaults.ripeGovVaultConfigs[RIPE].asset",
    "Defaults.trainingWheels",
    "Defaults.assetConfigs[GREEN].asset",
    "Defaults.assetConfigs[RIPE].asset",
    "Defaults.assetConfigs[SGREEN].asset",
    "Defaults.priorityStabVaults[1].asset",
)
# This ten-line block deliberately preserves reviewed cadence line anchors.
# Profile 1 excludes the RIPE/WETH governance-vault identity.
# Profile 1 excludes both GREEN/USDG and RIPE/WETH asset identities.
# Profile 1 excludes both LP deposit-limit and minimum-balance bindings.
# Profile 1 excludes the RIPE/WETH stability-vault identity.
# Profile 2 owns both later LP admissions under separate activation authority.
# Authority: docs/chains/rh/reassessment-and-qualification-synthesis.md.
# The complete manifest schema is retained for later Profile 2 authority.
# Deferred rows are not unresolved Profile 1 generation paths.
# Closure tests below prove they cannot reach the Profile 1 render.


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_robinhood_defaults",
        GENERATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_generator()


@pytest.fixture(scope="module")
def manifest():
    return GENERATOR.load_manifest(MANIFEST_PATH)


def _lookup(manifest):
    return {
        record["destination"]["path"]: record
        for record in manifest["parameters"]
    }


def _synthetic_manifest(manifest):
    bound = copy.deepcopy(manifest)
    address_by_symbol = {
        "[RIPE]": "0x1111111111111111111111111111111111111101",
        # Profile 2 LP rows deliberately have no synthetic address binding.
        "[GREEN]": "0x1111111111111111111111111111111111111103",
        "[SGREEN]": "0x1111111111111111111111111111111111111104",
        # Keep deferred LP identities unreachable from Profile 1 rendering.
    }
    next_address = 0x1200
    required = set(GENERATOR.required_generation_paths())
    for record in bound["parameters"]:
        path = record["destination"]["path"]
        if path not in required or record["status"] not in {"blocked", "unresolved"}:
            continue
        kind = record["unit"]["kind"]
        if kind == "address":
            raw = next(
                (
                    address
                    for marker, address in address_by_symbol.items()
                    if marker in path
                ),
                f"0x{next_address:040x}",
            )
            next_address += 1
        elif kind == "boolean":
            raw = False
        elif kind == "registry_id":
            raw = "[1]" if path.endswith(".vaultIds") else 1
        else:
            raw = 1
        schedule_id = record["approval"]["schedule_id"]
        record["value"] = {"kind": "concrete", "raw": raw}
        record["status"] = "approved"
        record["approval"] = {
            "status": "approved",
            "date": "2026-07-28",
            "provenance": "synthetic rendering fixture",
            "schedule_id": schedule_id,
        }
        record["blockers"] = []
        record["zero_semantics"] = (
            {
                "kind": "legitimate_false",
                "explanation": "Synthetic explicit false.",
            }
            if raw is False
            else {
                "kind": "not_zero",
                "explanation": "Synthetic nonzero binding.",
            }
        )
        record["base_comparison"] = {
            "kind": "not_applicable",
            "detail": "Synthetic fixture has no production comparison.",
        }
        record["conversion"] = {"kind": "identity"}
        record["generated_repr"] = {
            "kind": "vyper",
            "repr": "False" if raw is False else str(raw),
        }
    GENERATOR.validate_manifest(bound, require_canonical_state=False)
    return bound


def _mutated(manifest):
    return copy.deepcopy(manifest)


def _assert_code(manifest, code):
    with pytest.raises(GENERATOR.ManifestError, match=code):
        GENERATOR.validate_manifest(manifest)


def test_manifest_validates_as_one_closed_canonical_document(manifest):
    assert GENERATOR.validate_manifest(manifest) is manifest
    assert len(manifest["parameters"]) == 428
    assert list(manifest) == [
        "schema_version",
        "baseline",
        "decision_registry",
        "binding_schedules",
        "parameters",
    ]
    assert manifest["schema_version"] == "h04-robinhood-parameters-v2"


def test_every_record_has_exactly_the_approved_nineteen_keys(manifest):
    expected = set(GENERATOR.RECORD_KEYS)
    assert len(expected) == 19
    assert all(set(record) == expected for record in manifest["parameters"])


def test_manifest_contains_no_json_null_or_missing_field_equivalence():
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    assert ": null" not in raw
    assert "\u0000" not in raw
    assert json.loads(raw)["parameters"]


def test_complete_109_leaf_and_17_selector_census(manifest):
    defaults = [
        record["destination"]["path"]
        for record in manifest["parameters"]
        if record["destination"]["kind"] == "defaults_field"
    ]
    normalized = {
        GENERATOR.re.sub(r"\[[^]]+\]", "[*]", path) for path in defaults
    }
    assert len(normalized) == 109
    assert normalized == set(GENERATOR.canonical_default_templates())
    assert len(GENERATOR.default_selectors()) == 17
    assert len(defaults) == 305


def test_all_twenty_two_deployment_only_rows_are_covered(manifest):
    rows = {
        record["destination"]["path"].split(".")[1]
        for record in manifest["parameters"]
        if record["destination"]["path"].startswith("Deployment.DP-")
    }
    assert rows == {f"DP-{number:02d}" for number in range(1, 23)}


def test_ids_destinations_and_order_are_unique_and_canonical(manifest):
    ids = [record["id"] for record in manifest["parameters"]]
    paths = [record["destination"]["path"] for record in manifest["parameters"]]
    assert ids == [f"P-H04-{number:03d}" for number in range(1, 429)]
    assert len(paths) == len(set(paths))
    assert tuple(paths[:305]) == GENERATOR.canonical_default_paths()


def test_group_two_general_debt_and_auction_values_are_exact(manifest):
    records = _lookup(manifest)
    expected = {
        "Defaults.genConfig.perUserMaxVaults": 5,
        "Defaults.genConfig.perUserMaxAssetsPerVault": 15,
        "Defaults.genConfig.priceStaleTime": 86_400,
        "Defaults.genDebtConfig.perUserDebtLimit": "20000000000000000000000",
        "Defaults.genDebtConfig.globalDebtLimit": "200000000000000000000000",
        "Defaults.genDebtConfig.numBlocksPerInterval": 7_200,
        "Defaults.genDebtConfig.increasePerDangerBlock": 10,
        "Defaults.genDebtConfig.genAuctionParams.duration": 7_200,
    }
    for path, value in expected.items():
        assert records[path]["value"]["raw"] == value
    for field in GENERATOR.GEN_CONFIG_FIELDS[3:]:
        assert records[f"Defaults.genConfig.{field}"]["value"]["raw"] is True


def test_rewards_bonds_hr_and_underscore_preserve_inert_launch_posture(manifest):
    records = _lookup(manifest)
    for field in GENERATOR.REWARD_FIELDS:
        record = records[f"Defaults.rewardsConfig.{field}"]
        assert record["status"] == "disabled"
        assert record["value"]["raw"] in (0, False)
    assert records["Defaults.ripeBondConfig.canBond"]["value"]["raw"] is False
    assert records["Defaults.ripeBondConfig.epochLength"]["value"]["raw"] == 2_400
    assert records["Defaults.hrConfig.maxCompensation"]["value"]["raw"] == 0
    assert records["Defaults.underscoreRegistry"]["value"]["raw"] == "empty(address)"
    assert records["Defaults.shouldCheckLastTouch"]["value"]["raw"] is True


def test_product_graph_posture_is_explicit(manifest):
    records = _lookup(manifest)
    assert records["Defaults.assetConfigs[AAPL].asset"]["status"] == "omitted"
    assert records["Defaults.assetConfigs[USDG].asset"]["status"] == (
        "not_applicable"
    )
    assert records["Defaults.assetConfigs[GREEN_USDG_LP].config.debtTerms.ltv"][
        "value"
    ]["raw"] == 0
    assert records["Defaults.assetConfigs[RIPE_WETH_LP].config.debtTerms.ltv"][
        "value"
    ]["raw"] == 0
    assert records["Deployment.DP-20.teller.shouldPause"]["value"]["raw"] is True
    assert records["Deployment.DP-16.ccip.greenEnabled"]["value"]["raw"] is False


def test_decision_lifecycle_is_twenty_approved_zero_open_and_one_retired(
    manifest,
):
    registry = manifest["decision_registry"]
    approved = [
        decision["id"]
        for decision in registry
        if decision["status"] == "approved"
    ]
    assert approved == [
        *(f"D-H04-{number:02d}" for number in range(1, 19)),
        "D-H04-20",
        "D-H04-21",
    ]
    assert [
        decision
        for decision in registry
        if decision["status"] != "approved"
    ] == [
        {
            "id": "D-H04-19",
            "status": "retired_non_operative",
            "operative": False,
        }
    ]
    assert not any(
        record["approval"]["status"] == "pending"
        for record in manifest["parameters"]
    )
    assert all(
        record["value"]["kind"] in {"typed_null", "derived"}
        for record in manifest["parameters"]
        if record["status"] in {"blocked", "unresolved", "derived"}
    )


def test_zero_false_blocked_deferred_omitted_and_missing_are_distinct(manifest):
    records = _lookup(manifest)
    assert records["Defaults.ripeAvailForRewards"]["value"] == {
        "kind": "concrete",
        "raw": 0,
    }
    assert records["Defaults.rewardsConfig.arePointsEnabled"]["value"] == {
        "kind": "concrete",
        "raw": False,
    }
    assert records["Defaults.trainingWheels"]["value"]["kind"] == "typed_null"
    assert records["Defaults.trainingWheels"]["status"] == "blocked"
    assert records["Deployment.DP-18.roles.liteSigners"]["value"] == {
        "kind": "concrete",
        "raw": "[]",
    }
    assert records["Deployment.DP-18.roles.liteSigners"]["zero_semantics"][
        "kind"
    ] == "legitimate_empty"
    deferred = records["Deployment.DP-22.bondBooster.minLockDuration"]
    assert deferred["status"] == "approved"
    assert deferred["launch_phase"] == "post-launch release"
    omitted = records["Defaults.priorityLiqAssetVaults[0].vaultId"]
    assert omitted["status"] == "omitted"
    assert omitted["value"]["kind"] == "typed_null"

    missing = _mutated(manifest)
    del missing["parameters"][0]["status"]
    _assert_code(missing, "H04_RECORD_KEYS")


def test_psm_is_disabled_and_every_numeric_or_capacity_value_is_blocked(manifest):
    records = _lookup(manifest)
    assert records["Deployment.DP-07.psm.constructor.canMint"]["value"]["raw"] is (
        False
    )
    assert records[
        "Deployment.DP-07.psm.constructor.canRedeem"
    ]["value"]["raw"] is False
    assert records[
        "Deployment.DP-07.psm.constructor.shouldAutoDeposit"
    ]["value"]["raw"] is True
    assert records[
        "Deployment.DP-07.psm.preActivation.shouldAutoDeposit"
    ]["value"]["raw"] is False
    assert all(
        records[f"Deployment.DP-08.psm.{field}"]["status"] == "blocked"
        for field in (
            "mintFee",
            "redeemFee",
            "maxMintPerInterval",
            "maxRedeemPerInterval",
            "numBlocksPerInterval",
            "allowlists",
            "reserveFunding",
        )
    )


def test_s3_s4_s5_bindings_are_assertion_only_or_blocked(manifest):
    records = _lookup(manifest)
    assert records[
        "Deployment.DP-01.lootbox.minUnderscoreSendInterval"
    ]["destination"]["kind"] == "assertion"
    s4 = records["Deployment.DP-03.deleverage.deleverageCooldown"]
    assert s4["value"]["raw"] == 0
    assert "activation requires reopening S4" in s4["description"]
    assert records[
        "Deployment.DP-04.ledger.actionBlockSourceSemantic"
    ]["value"]["raw"] == "0x64"
    assert records[
        "Deployment.DP-04.ledger.actionBlockSourceBinding"
    ]["status"] == "blocked"


def test_block_conversion_zero_minimum_and_seconds_separation():
    assert GENERATOR.convert_base_blocks(0) == 0
    assert GENERATOR.convert_base_blocks(1) == 1
    assert GENERATOR.convert_base_blocks(6) == 1
    assert GENERATOR.convert_base_blocks(7) == 2
    assert GENERATOR.convert_base_blocks(43_200) == 7_200
    with pytest.raises(GENERATOR.ManifestError, match="H04_BLOCK_CONVERSION_INPUT"):
        GENERATOR.convert_base_blocks(-1)


def test_rate_per_block_danger_slope_is_never_converted(manifest):
    record = _lookup(manifest)[
        "Defaults.genDebtConfig.increasePerDangerBlock"
    ]
    assert record["unit"] == {
        "kind": "rate_per_block_1e6",
        "denominator": 1_000_000,
    }
    assert record["conversion"] == {"kind": "identity"}


def test_real_manifest_fails_closed_without_creating_output_or_temporary_file(
    manifest,
):
    assert not REAL_OUTPUT.exists()
    before = set(REAL_OUTPUT.parent.iterdir())
    with pytest.raises(
        GENERATOR.ManifestError,
        match=r"H04_UNRESOLVED_GENERATION:",
    ):
        GENERATOR.render_defaults(manifest)
    assert not REAL_OUTPUT.exists()
    assert set(REAL_OUTPUT.parent.iterdir()) == before


def test_exact_profile1_generation_bearers_are_blocked_deterministically(
    manifest,
):
    records = _lookup(manifest)
    blocked = tuple(
        path
        for path in GENERATOR.required_generation_paths()
        if records[path]["status"] in {"blocked", "unresolved"}
    )
    assert blocked == EXPECTED_GENERATION_BLOCKERS
    assert len(blocked) == 6
    assert all(records[path]["value"]["kind"] == "typed_null" for path in blocked)
    assert "Defaults.liteSigners[0]" not in GENERATOR.required_generation_paths()


@pytest.mark.parametrize("remaining", EXPECTED_GENERATION_BLOCKERS)
def test_closing_fewer_than_all_generation_blockers_never_renders(
    manifest,
    remaining,
):
    candidate = _synthetic_manifest(manifest)
    candidate_record = _lookup(candidate)[remaining]
    original_record = _lookup(manifest)[remaining]
    candidate_record.clear()
    candidate_record.update(copy.deepcopy(original_record))
    GENERATOR.validate_manifest(candidate, require_canonical_state=False)
    with pytest.raises(
        GENERATOR.ManifestError,
        match="H04_UNRESOLVED_GENERATION:" + GENERATOR.re.escape(remaining),
    ):
        GENERATOR.render_defaults(candidate)
    assert not REAL_OUTPUT.exists()


def test_real_check_only_command_is_stable_and_output_free():
    command = [sys.executable, str(GENERATOR_PATH), "--check"]
    first = subprocess.run(
        command,
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        command,
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == second.returncode == 2
    assert first.stdout == second.stdout
    assert first.stdout.startswith(
        "H04_BLOCKED: H04_UNRESOLVED_GENERATION:"
    )
    assert first.stderr == second.stderr == ""
    assert not REAL_OUTPUT.exists()


def test_stale_defaults_is_rejected_before_check_render(
    manifest,
    monkeypatch,
    tmp_path,
):
    manifest_path = tmp_path / "robinhood-parameters.json"
    output = tmp_path / "DefaultsRobinhood.vy"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(
        GENERATOR,
        "_repository_paths",
        lambda: (manifest_path, output),
    )
    assert GENERATOR.main(["--check"]) == 2
    assert output.read_text(encoding="utf-8") == "stale\n"


def test_synthetic_render_is_byte_identical_across_repeated_runs(manifest):
    synthetic = _synthetic_manifest(manifest)
    first = GENERATOR.render_defaults(synthetic)
    second = GENERATOR.render_defaults(copy.deepcopy(synthetic))
    assert first == second
    assert hashlib.sha256(first.encode()).hexdigest() == hashlib.sha256(
        second.encode()
    ).hexdigest()
    assert all(marker not in first for marker in ("DefaultsBase", "DefaultsLocal"))
    assert all(marker not in first for marker in ("GREEN_USDG_LP", "RIPE_WETH_LP"))
    assert (
        "def liteSigners() -> DynArray[address, 10]:\n"
        "    return []\n"
    ) in first
    assert "Defaults.liteSigners[0]" not in first


def test_two_process_synthetic_determinism(manifest, tmp_path):
    synthetic_path = tmp_path / "synthetic.json"
    synthetic_path.write_text(
        json.dumps(_synthetic_manifest(manifest), sort_keys=True),
        encoding="utf-8",
    )
    program = (
        "import hashlib,importlib.util,json,pathlib;"
        f"p=pathlib.Path({str(GENERATOR_PATH)!r});"
        "s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        f"d=json.loads(pathlib.Path({str(synthetic_path)!r}).read_text());"
        "print(hashlib.sha256(m.render_defaults(d).encode()).hexdigest())"
    )
    outputs = [
        subprocess.run(
            [sys.executable, "-c", program],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        for _ in range(2)
    ]
    assert outputs[0] == outputs[1]


def test_two_clean_export_roots_render_identically(manifest, tmp_path):
    synthetic = _synthetic_manifest(manifest)
    digests = []
    for name in ("checkout-a", "checkout-b"):
        root = tmp_path / name
        root.mkdir()
        fixture = root / "manifest.json"
        fixture.write_text(
            json.dumps(synthetic, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        digests.append(
            hashlib.sha256(
                GENERATOR.render_defaults(
                    json.loads(fixture.read_text(encoding="utf-8"))
                ).encode()
            ).hexdigest()
        )
    assert digests[0] == digests[1]


def test_atomic_replacement_uses_same_directory_only(
    manifest,
    monkeypatch,
    tmp_path,
):
    rendered = GENERATOR.render_defaults(_synthetic_manifest(manifest))
    output = tmp_path / "DefaultsRobinhood.vy"
    calls = []
    original = os.replace

    def observed(source, destination):
        calls.append((Path(source), Path(destination)))
        original(source, destination)

    monkeypatch.setattr(GENERATOR.os, "replace", observed)
    GENERATOR.atomic_replace_output(
        rendered,
        output,
        canonical_output=output,
    )
    assert output.read_text(encoding="utf-8") == rendered
    assert len(calls) == 1
    assert calls[0][0].parent == calls[0][1].parent == tmp_path
    assert not list(tmp_path.glob(".DefaultsRobinhood.*.tmp"))


@pytest.mark.parametrize(
    "name",
    ("DefaultsBase.vy", "DefaultsLocal.vy", "Elsewhere.vy"),
)
def test_every_noncanonical_target_is_refused(name, tmp_path):
    output = tmp_path / name
    with pytest.raises(
        GENERATOR.ManifestError,
        match="H04_(?:FORBIDDEN|NONCANONICAL)_TARGET",
    ):
        GENERATOR.atomic_replace_output(
            "unchanged",
            output,
            canonical_output=output,
        )
    assert not output.exists()


def test_failed_target_check_leaves_existing_output_untouched(tmp_path):
    output = tmp_path / "DefaultsRobinhood.vy"
    output.write_text("existing\n", encoding="utf-8")
    with pytest.raises(GENERATOR.ManifestError, match="H04_NONCANONICAL_TARGET"):
        GENERATOR.atomic_replace_output(
            "replacement",
            output,
            canonical_output=tmp_path / "different" / "DefaultsRobinhood.vy",
        )
    assert output.read_text(encoding="utf-8") == "existing\n"


def test_generator_imports_only_the_standard_library():
    tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imports <= {
        "__future__",
        "argparse",
        "collections",
        "hashlib",
        "json",
        "os",
        "re",
        "tempfile",
        "pathlib",
        "typing",
    }


def test_exact_semantic_census_and_approval_branches(manifest):
    assert GENERATOR.Counter(
        record["status"] for record in manifest["parameters"]
    ) == GENERATOR.Counter(
        {
            "approved": 152,
            "disabled": 150,
            "omitted": 34,
            "blocked": 60,
            "derived": 1,
            "not_applicable": 31,
        }
    )
    assert GENERATOR.Counter(
        record["approval"]["status"] for record in manifest["parameters"]
    ) == GENERATOR.Counter({"approved": 367, "pending_binding": 61})


def test_registry_v1_exact_mapping_reverse_ownership_and_digest(manifest):
    schedules = manifest["binding_schedules"]
    assert schedules == GENERATOR.EXPECTED_BINDING_SCHEDULES
    assert len(schedules) == 14
    assert sum(len(schedule["records"]) for schedule in schedules) == 61
    assert GENERATOR.binding_schedules_digest(schedules) == (
        "f6605710bb6a3f7274d66bfcbb8104fdd21f9a78cf043736474a2f5a6e14e167"
    )
    records = {record["id"]: record for record in manifest["parameters"]}
    owners = {}
    for schedule in schedules:
        for record_id in schedule["records"]:
            assert record_id not in owners
            owners[record_id] = schedule["id"]
            assert records[record_id]["approval"] == {
                "status": "pending_binding",
                "schedule_id": schedule["id"],
            }
    assert len(owners) == 61


def test_exact_owner_policy_transitions_are_concrete_or_omitted(manifest):
    records = {record["id"]: record for record in manifest["parameters"]}
    assert records["P-H04-305"]["status"] == "omitted"
    assert records["P-H04-305"]["value"]["kind"] == "typed_null"
    assert records["P-H04-305"]["blockers"] == []
    assert records["P-H04-412"]["value"] == {
        "kind": "concrete",
        "raw": "[]",
    }
    assert records["P-H04-412"]["unit"] == {"kind": "address"}
    assert records["P-H04-412"]["blockers"] == []
    for record_id in ("P-H04-415", "P-H04-417", "P-H04-419"):
        assert records[record_id]["value"] == {"kind": "concrete", "raw": 0}
        assert records[record_id]["zero_semantics"]["kind"] == "legitimate_zero"
        assert records[record_id]["blockers"] == []
    assert all(
        records[f"P-H04-{number:03d}"]["status"] == "omitted"
        and records[f"P-H04-{number:03d}"]["blockers"] == []
        for number in range(81, 112)
    )


def test_policy_approval_never_supplies_concrete_scheduled_bindings(manifest):
    records = {record["id"]: record for record in manifest["parameters"]}
    scheduled = {
        record_id
        for schedule in manifest["binding_schedules"]
        for record_id in schedule["records"]
    }
    assert all(
        records[record_id]["approval"]["status"] == "pending_binding"
        for record_id in scheduled
    )
    assert all(
        records[record_id]["status"]
        in {"blocked", "derived"}
        for record_id in scheduled
    )
    assert not any(
        blocker.startswith("D-H04-")
        for record in manifest["parameters"]
        for blocker in record["blockers"]
    )


def test_parked_schedules_cannot_be_mistaken_for_release_bindings(manifest):
    schedules = {
        schedule["id"]: schedule for schedule in manifest["binding_schedules"]
    }
    assert {
        schedule_id
        for schedule_id, schedule in schedules.items()
        if schedule["classification"] == "parked"
    } == {
        "BS-H04-STOCK-ACTIVATION-PARKED",
        "BS-H04-CCIP-PARKED",
    }
    assert all(
        schedule["closure_artifacts"][0]
        == "cannot close under current authority"
        for schedule in schedules.values()
        if schedule["classification"] == "parked"
    )


def test_lite_signer_policy_crosses_defaults_and_deployment_boundaries(
    manifest,
):
    records = _lookup(manifest)
    default = records["Defaults.liteSigners[0]"]
    deployment = records["Deployment.DP-18.roles.liteSigners"]
    assert default["status"] == "omitted"
    assert default["value"]["kind"] == "typed_null"
    assert deployment["status"] == "approved"
    assert deployment["value"]["raw"] == "[]"
    assert "Defaults.liteSigners[0]" in GENERATOR.canonical_default_paths()
    assert "Defaults.liteSigners[0]" not in GENERATOR.required_generation_paths()


def test_zero_premints_do_not_approve_recipients_or_later_issuance(manifest):
    records = {record["id"]: record for record in manifest["parameters"]}
    for amount, recipient in (
        ("P-H04-415", "P-H04-416"),
        ("P-H04-417", "P-H04-418"),
        ("P-H04-419", "P-H04-420"),
    ):
        assert records[amount]["value"] == {"kind": "concrete", "raw": 0}
        assert records[recipient]["status"] == "blocked"
        assert records[recipient]["value"]["kind"] == "typed_null"
        assert records[recipient]["approval"]["schedule_id"] == (
            "BS-H04-SUPPLY-RECIPIENTS-OP"
        )


def test_stock_defaults_are_launch_omissions_not_future_values(manifest):
    records = {record["id"]: record for record in manifest["parameters"]}
    omitted = [records[f"P-H04-{number:03d}"] for number in range(81, 112)]
    assert len(omitted) == 31
    assert all(record["status"] == "omitted" for record in omitted)
    assert all(record["value"]["kind"] == "typed_null" for record in omitted)
    assert all(record["launch_phase"] == "omitted" for record in omitted)
    assert all(not record["blockers"] for record in omitted)
    parked = next(
        schedule
        for schedule in manifest["binding_schedules"]
        if schedule["id"] == "BS-H04-STOCK-ACTIVATION-PARKED"
    )
    assert len(parked["records"]) == 17
    assert set(parked["records"]).isdisjoint(
        {record["id"] for record in omitted}
    )


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("decision_open", "H04_DECISION_LIFECYCLE"),
        ("decision_typo", "H04_DECISION_LIFECYCLE"),
        ("old_pending", "H04_APPROVAL_STATUS"),
        ("unknown_schedule", "H04_UNKNOWN_SCHEDULE_ID"),
        ("reverse_schedule", "H04_SCHEDULE_REVERSE_REFERENCE"),
        ("duplicate_ownership", "H04_DUPLICATE_SCHEDULE_OWNERSHIP"),
        ("missing_ownership", "H04_BINDING_SCHEDULE_CENSUS"),
        ("schedule_semantics", "H04_BINDING_SCHEDULE_SEMANTICS"),
        ("decision_blocker", "H04_UNKNOWN_BLOCKER"),
        ("lite_policy", "H04_LITE_SIGNER_POLICY"),
        ("lite_cross_boundary", "H04_LITE_SIGNER_CROSS_BOUNDARY"),
        ("premint", "H04_NO_PREMINT_POLICY"),
        ("stock_omission", "H04_STOCK_LAUNCH_OMISSION"),
    ],
)
def test_v2_lifecycle_schedule_and_policy_mutations_fail_closed(
    manifest,
    mutation,
    code,
):
    candidate = _mutated(manifest)
    records = {record["id"]: record for record in candidate["parameters"]}
    if mutation == "decision_open":
        candidate["decision_registry"][11]["status"] = "open"
    elif mutation == "decision_typo":
        candidate["decision_registry"][0]["id"] = "D-H04-001"
    elif mutation == "old_pending":
        records["P-H04-056"]["approval"] = {
            "status": "pending",
            "decision": "D-H04-15",
        }
    elif mutation == "unknown_schedule":
        records["P-H04-056"]["approval"]["schedule_id"] = "BS-H04-UNKNOWN"
    elif mutation == "reverse_schedule":
        records["P-H04-056"]["approval"]["schedule_id"] = (
            "BS-H04-LP-ARTIFACTS-RC"
        )
    elif mutation == "duplicate_ownership":
        candidate["binding_schedules"][1]["records"].append("P-H04-056")
    elif mutation == "missing_ownership":
        candidate["binding_schedules"][0]["records"].remove("P-H04-056")
    elif mutation == "schedule_semantics":
        candidate["binding_schedules"][0]["prerequisite"] += " drift"
    elif mutation == "decision_blocker":
        records["P-H04-056"]["blockers"].append("D-H04-15")
    elif mutation == "lite_policy":
        records["P-H04-305"]["status"] = "not_applicable"
    elif mutation == "lite_cross_boundary":
        records["P-H04-412"]["value"]["raw"] = "empty(address)"
        records["P-H04-412"]["zero_semantics"]["kind"] = "not_zero"
    elif mutation == "premint":
        records["P-H04-415"]["value"]["raw"] = 1
        records["P-H04-415"]["zero_semantics"]["kind"] = "not_zero"
    else:
        records["P-H04-081"]["launch_phase"] = "atomic Stock activation"
    _assert_code(candidate, code)


def test_registry_digest_is_independently_enforced(manifest, monkeypatch):
    monkeypatch.setattr(GENERATOR, "BINDING_SCHEDULES_SHA256", "0" * 64)
    _assert_code(manifest, "H04_BINDING_SCHEDULE_DIGEST")


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("top_key", "H04_TOP_KEYS"),
        ("record_key", "H04_RECORD_KEYS"),
        ("null", "H04_NULL_FORBIDDEN"),
        ("id_order", "H04_ID_ORDER"),
        ("destination_duplicate", "H04_DUPLICATE_DESTINATION"),
        ("h03", "H04_H03_REFERENCE"),
        ("status_value", "H04_STATUS_VALUE_KIND"),
        ("unit", "H04_UNIT_KIND"),
        ("zero", "H04_ZERO_UNTYPED"),
        ("false", "H04_FALSE_UNTYPED"),
        ("block_conversion", "H04_BLOCK_CONVERSION"),
        ("seconds_conversion", "H04_SECONDS_CONVERSION"),
        ("rate_conversion", "H04_DANGER_SLOPE_CONVERSION"),
        ("unknown_blocker", "H04_UNKNOWN_BLOCKER"),
        ("missing_blocker", "H04_MISSING_BLOCKER"),
        ("base_address", "H04_BASE_ADDRESS_LEAK"),
        ("zero_address", "H04_ZERO_ADDRESS_LITERAL"),
        ("forbidden_text", "H04_FORBIDDEN_TEXT"),
        ("allocation", "H04_REWARD_ALLOCATION"),
        ("default_order", "H04_DEFAULT_ORDER_OR_CENSUS"),
    ],
)
def test_closed_schema_and_cross_record_rejections(manifest, mutation, code):
    candidate = _mutated(manifest)
    records = candidate["parameters"]
    lookup = _lookup(candidate)
    if mutation == "top_key":
        candidate["extra"] = True
    elif mutation == "record_key":
        records[0]["extra"] = True
    elif mutation == "null":
        records[0]["description"] = None
    elif mutation == "id_order":
        records[0]["id"] = "P-H04-999"
    elif mutation == "destination_duplicate":
        records[1]["destination"]["path"] = records[0]["destination"]["path"]
    elif mutation == "h03":
        records[0]["h03_ref"] = "CM-061"
    elif mutation == "status_value":
        records[0]["status"] = "blocked"
    elif mutation == "unit":
        records[0]["unit"] = {"kind": "unknown"}
    elif mutation == "zero":
        lookup["Defaults.ripeAvailForRewards"]["zero_semantics"] = {
            "kind": "not_zero",
            "explanation": "invalid",
        }
    elif mutation == "false":
        lookup["Defaults.rewardsConfig.arePointsEnabled"]["zero_semantics"] = {
            "kind": "not_zero",
            "explanation": "invalid",
        }
    elif mutation == "block_conversion":
        lookup["Defaults.ripeBondConfig.epochLength"]["conversion"][
            "rh_blocks"
        ] = 2_401
    elif mutation == "seconds_conversion":
        lookup["Defaults.genConfig.priceStaleTime"]["conversion"] = {
            "kind": "identity"
        }
    elif mutation == "rate_conversion":
        lookup["Defaults.genDebtConfig.increasePerDangerBlock"]["conversion"] = {
            "kind": "not_applicable"
        }
    elif mutation == "unknown_blocker":
        lookup["Defaults.trainingWheels"]["blockers"].append("B-UNKNOWN")
    elif mutation == "missing_blocker":
        lookup["Defaults.trainingWheels"]["blockers"] = []
    elif mutation == "base_address":
        records[0]["description"] = next(
            iter(GENERATOR.FORBIDDEN_BASE_ADDRESSES)
        )
    elif mutation == "zero_address":
        records[0]["description"] = "0x" + ("0" * 40)
    elif mutation == "forbidden_text":
        records[0]["description"] = "TBD"
    elif mutation == "allocation":
        record = lookup["Defaults.rewardsConfig.borrowersAlloc"]
        record["value"]["raw"] = 1
        record["zero_semantics"] = {
            "kind": "not_zero",
            "explanation": "invalid",
        }
        record["generated_repr"]["repr"] = "1"
    else:
        records[0], records[1] = records[1], records[0]
        records[0]["id"], records[1]["id"] = records[1]["id"], records[0]["id"]
    _assert_code(candidate, code)


@pytest.mark.parametrize(
    ("path", "raw", "code"),
    (
        (
            "Deployment.DP-03.deleverage.futureValue",
            None,
            "H04_DELEVERAGE_REPRESENTATION",
        ),
        (
            "Deployment.DP-03.fullPayoffBuffer",
            None,
            "H04_DELEVERAGE_REPRESENTATION",
        ),
        (
            "Deployment.DP-03.payoff.overageBps",
            None,
            "H04_DELEVERAGE_REPRESENTATION",
        ),
        (
            "Deployment.DP-03.dust.dustThreshold",
            None,
            "H04_DELEVERAGE_REPRESENTATION",
        ),
        (
            "Deployment.DP-03.dust.dustBps",
            None,
            "H04_DELEVERAGE_REPRESENTATION",
        ),
        (
            "Deployment.DP-03.fullPayoffBuffer",
            10**15,
            "H04_BASE_DELEVERAGE_VALUE",
        ),
        (
            "Deployment.DP-03.payoff.overageBps",
            100,
            "H04_BASE_DELEVERAGE_VALUE",
        ),
    ),
)
def test_deleverage_representation_and_base_values_fail_closed(
    manifest,
    path,
    raw,
    code,
):
    candidate = _mutated(manifest)
    record = candidate["parameters"][-1]
    record["destination"]["path"] = path
    if raw is not None:
        record["value"]["raw"] = raw
        record["conversion"] = {"kind": "identity"}
    _assert_code(candidate, code)


def test_profile1_render_projection_is_exact_and_schema_bounded(manifest):
    assert GENERATOR.PROFILE1_GOV_ROWS == ("RIPE",)
    assert GENERATOR.PROFILE1_ASSET_ROWS == ("GREEN", "RIPE", "SGREEN")
    assert GENERATOR.PROFILE1_STAB_VAULT_INDEXES == (1,)
    assert set(GENERATOR.PROFILE1_GOV_ROWS) <= set(GENERATOR.GOV_ROWS)
    assert set(GENERATOR.PROFILE1_ASSET_ROWS) <= set(GENERATOR.ASSET_ROWS)
    canonical = set(GENERATOR.canonical_default_paths())
    required = set(GENERATOR.required_generation_paths())
    deferred = {
        path
        for path in canonical
        if "[GREEN_USDG_LP]" in path
        or "[RIPE_WETH_LP]" in path
        or path.startswith("Defaults.priorityStabVaults[0].")
    }
    records = _lookup(manifest)
    assert len(deferred) == 72
    assert hashlib.sha256(
        ("\n".join(sorted(deferred)) + "\n").encode()
    ).hexdigest() == (
        "1b1fa2c5f0b4626b05bdb86eeb7b713ca9487e53fa3880ff1707647a6355aa98"
    )
    assert deferred.isdisjoint(required)
    assert sum(records[path]["status"] == "approved" for path in deferred) == 18
    assert sum(records[path]["status"] == "disabled" for path in deferred) == 44
    assert sum(records[path]["status"] == "blocked" for path in deferred) == 10
    assert all(
        records[path]["value"]["kind"] == "concrete"
        for path in deferred
        if records[path]["status"] == "approved"
    )
    rendered = GENERATOR.render_defaults(_synthetic_manifest(manifest))
    assert "GREEN_USDG_LP" not in rendered
    assert "RIPE_WETH_LP" not in rendered


def test_profile1_projection_authority_is_current_and_hash_bound():
    authority = REPOSITORY / GENERATOR.PROFILE1_AUTHORITY_PATH
    current = authority.read_bytes()
    introduced = subprocess.run(
        [
            "/usr/bin/git",
            "show",
            (
                f"{GENERATOR.PROFILE1_AUTHORITY_COMMIT}:"
                f"{GENERATOR.PROFILE1_AUTHORITY_PATH}"
            ),
        ],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
    ).stdout
    assert hashlib.sha256(current).hexdigest() == (
        GENERATOR.PROFILE1_AUTHORITY_SHA256
    )
    assert introduced == current


def test_blocked_typed_null_deleverage_name_uses_normal_command_contract(
    manifest,
    tmp_path,
):
    candidate = _mutated(manifest)
    record = next(
        item for item in candidate["parameters"] if item["id"] == "P-H04-393"
    )
    assert record["status"] == "blocked"
    assert record["value"]["kind"] == "typed_null"
    assert "raw" not in record["value"]
    record["destination"]["path"] = "Deployment.DP-14.lp.dustThreshold"

    repository = tmp_path / "repo"
    script = repository / "scripts/params/generate_robinhood_defaults.py"
    manifest_path = repository / "config/robinhood-parameters.json"
    output = repository / "contracts/config/DefaultsRobinhood.vy"
    script.parent.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    script.write_bytes(GENERATOR_PATH.read_bytes())
    manifest_path.write_text(json.dumps(candidate), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert result.stdout == "H04_BLOCKED: H04_DELEVERAGE_REPRESENTATION\n"
    assert result.stderr == ""
    assert not output.exists()
