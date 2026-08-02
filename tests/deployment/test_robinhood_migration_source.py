from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from scripts.utils.deployment_assertions import (
    DeploymentAssertionInputError,
    assert_deployment,
    expectations_from_plan,
)
from scripts.utils.migration_runner import (
    MigrationPlanError,
    build_robinhood_plan,
    canonical_jcs_bytes,
    load_robinhood_stages,
    read_bound_h06_history,
    robinhood_source_expectations,
    validate_execution_plan_artifact,
    validate_plan_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
STAGE_IDS = [
    "0010", "0020", "0030", "0040", "0050", "0060", "0070", "0080",
    "0100", "0200", "0300", "0400", "0500", "0600", "0700", "0800", "0900",
]


def _synthetic(profile_id="robinhood-mainnet"):
    return build_robinhood_plan(
        profile_id,
        repository_root=ROOT,
        synthetic_bind_all=True,
    )


def _actions(plan):
    return [action for stage in plan["stages"] for action in stage["actions"]]


def _action(plan, semantic_id):
    return next(
        action for action in _actions(plan)
        if action["semantic_action_id"] == semantic_id
    )


def test_shared_source_manifest_is_exact_and_1000_is_deferred_only():
    expectations = robinhood_source_expectations()
    assert [item.migration_id for item in expectations] == STAGE_IDS
    assert [stage["migration_id"] for stage in load_robinhood_stages(ROOT)] == STAGE_IDS
    assert not (ROOT / "migrations/robinhood/1000_CcipPoolsAndRegistration.py").exists()


def test_current_integrated_authority_builds_all_steps_with_canonical_curve_blockers():
    from config import BluePrint as blueprint

    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    assert plan["status"] == "blocked"
    assert plan["plan_hash"] is None
    assert "H05_CURVE_LAUNCH_AUTHORITY_PENDING" not in plan["blockers"]
    curve_blockers = [
        detail
        for detail in plan["blocker_details"]
        if detail["key"].startswith("H05_CURVE_")
    ]
    assert len(curve_blockers) == 23
    assert len(blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS) == 39
    assert [stage["migration_id"] for stage in plan["stages"]] == STAGE_IDS
    assert all(stage["actions"] for stage in plan["stages"])


def test_fully_bound_synthetic_plan_is_complete_and_deterministic():
    first = _synthetic()
    second = _synthetic()
    assert first == second
    assert first["status"] == "proof-complete"
    assert len(first["blockers"]) == 99
    assert first["plan_hash"] is None
    assert len(first["proof_hash"]) == 64
    assert first["artifact"] == {
        "kind": "synthetic-proof",
        "profile_kind": "synthetic-proof",
        "production": False,
        "executable": False,
        "history_eligible": False,
        "identity_domain": "ripe-robinhood-synthetic-proof-v1",
    }
    assert first["profile"]["profile_id"] == "robinhood-synthetic-proof"
    assert first["profile"]["base_profile_id"] == "robinhood-mainnet"
    assert len(first["source"]["source_digest"]) == 64
    assert canonical_jcs_bytes(first) == canonical_jcs_bytes(second)
    coverage = first["component_coverage"]
    assert set(coverage["selected"]) | set(coverage["blocked"]) == set(
        coverage["represented"]
    )
    assert sum(
        action["kind"] == "deployment" for action in _actions(first)
    ) == 37
    assert len(first["registry_coverage"]) == 33


def test_curve_selection_or_registry_drift_fails_closed(monkeypatch):
    from config import BluePrint as blueprint

    components = tuple(
        replace(row, deployment_disposition="omitted", selection_state="omitted")
        if row.component_id == "CM-017" else row
        for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
    )
    monkeypatch.setattr(blueprint, "ROBINHOOD_COMPONENT_SELECTIONS", components)
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "_load_blueprint", lambda _root: blueprint)
    with pytest.raises(MigrationPlanError, match="H05_CURVE_AUTHORITY_MISMATCH"):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_missing_curve_launch_authority_row_has_stable_typed_error(
    monkeypatch,
):
    from config import BluePrint as blueprint

    monkeypatch.setattr(
        blueprint,
        "ROBINHOOD_CURVE_LAUNCH_INPUTS",
        tuple(
            row
            for row in blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
            if row.input_id != "launch.component"
        ),
    )
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "_load_blueprint", lambda _root: blueprint)
    with pytest.raises(
        MigrationPlanError, match="H05_CURVE_AUTHORITY_MISMATCH"
    ):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_wrong_curve_launch_chain_identity_fails_closed(monkeypatch):
    from config import BluePrint as blueprint

    monkeypatch.setattr(
        blueprint,
        "ROBINHOOD_CURVE_LAUNCH_INPUTS",
        tuple(
            replace(row, value=46630)
            if row.input_id == "launch.chain_id"
            else row
            for row in blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
        ),
    )
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "_load_blueprint", lambda _root: blueprint)
    with pytest.raises(
        MigrationPlanError, match="H05_CURVE_AUTHORITY_MISMATCH"
    ):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_fully_bound_generation_is_byte_identical_in_clean_processes():
    code = (
        "from pathlib import Path;"
        "from scripts.utils.migration_runner import build_robinhood_plan,canonical_jcs_bytes;"
        "p=build_robinhood_plan('robinhood-mainnet',repository_root=Path.cwd(),"
        "synthetic_bind_all=True);"
        "print(canonical_jcs_bytes(p).decode())"
    )
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            check=True,
            env={"LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert result.stderr == b""
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]
    assert hashlib.sha256(outputs[0]).hexdigest() == hashlib.sha256(outputs[1]).hexdigest()


def test_profiles_share_source_and_actions_but_keep_chain_identity_separate():
    mainnet = _synthetic("robinhood-mainnet")
    testnet = _synthetic("robinhood-testnet")
    assert mainnet["source"] == testnet["source"]
    assert mainnet["stages"] == testnet["stages"]
    assert mainnet["profile"]["expected_chain_id"] == 4663
    assert testnet["profile"]["expected_chain_id"] == 46630
    assert mainnet["proof_hash"] != testnet["proof_hash"]


def test_price_registry_order_priority_and_pre_registration_validation_are_exact():
    plan = _synthetic()
    registrations = [
        (action["component_id"], action["registry"]["registry_id"])
        for action in _actions(plan)
        if action["kind"] == "registration"
        and action["registry"]["domain"] == "price_desk"
    ]
    assert registrations == [("CM-016", 1), ("CM-017", 2), ("CM-018", 3)]
    action_ids = [action["semantic_action_id"] for action in _actions(plan)]
    assert action_ids.index("register-chainlink-prices") < action_ids.index("validate-direct-green-pricing")
    assert action_ids.index("validate-direct-green-pricing") < action_ids.index("register-curve-prices")
    assert action_ids.index("register-curve-prices") < action_ids.index("configure-curve-green-feed-at-id-two")
    assert action_ids.index("register-curve-prices") < action_ids.index("register-blue-chip-yield-prices")
    assert _action(plan, "apply-price-desk-priority")["postconditions"] == [
        "price-priority-is-one-three"
    ]


def test_curve_feed_is_green_only_and_pricing_graph_is_nonrecursive():
    configure = _action(_synthetic(), "configure-curve-green-feed-at-id-two")
    assert configure["requires"] == [
        "address:GREEN_TOKEN",
        "address:GREEN_USDG_CURVE_POOL",
        "action:register-curve-prices",
    ]
    assert "no-curve-usdg-feed" in configure["postconditions"]
    assert "green-resolves-through-curve-after-priority-miss" in configure["postconditions"]
    direct = _action(_synthetic(), "validate-direct-green-pricing")
    assert "pricing-recursion-detected" in direct["abort_if"]
    assert "pricing-graph-nonrecursive" in direct["postconditions"]


def test_curve_constructor_uses_exact_integrated_binding_authority():
    constructor = _action(
        _synthetic(), "deploy-curve-prices-unregistered"
    )["constructor"]
    assert constructor == [
        "address:RIPE_HQ",
        "input:Deployment.DP-18.roles.governance",
        "curve:curve.address_provider",
        "address:GREEN_TOKEN",
        "address:SGREEN_TOKEN",
        "curve-binding:_minPriceChangeTimeLock",
        "curve-binding:_maxPriceChangeTimeLock",
    ]


@pytest.mark.parametrize(
    "reference",
    (
        "curve:pool.address",
        "curve:pool.funding_source",
        "curve:pool.custodian",
        "curve:pool.slippage_limit",
    ),
)
def test_curve_external_controls_remain_individually_typed_blocked(reference):
    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    detail = next(
        item for item in plan["blocker_details"] if reference in item["references"]
    )
    assert detail["key"].startswith("H05_CURVE_")
    assert detail["key"].endswith("_PENDING")


def test_curve_stage_consumes_every_canonical_input_without_local_value_aliases():
    from config import BluePrint as blueprint

    canonical = {row.input_id for row in blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS}
    references = {
        reference[6:]
        for action in _actions(_synthetic())
        for reference in action.get("constructor", []) + action.get("requires", [])
        if reference.startswith("curve:")
    }
    assert references == canonical
    assert len(canonical) == 39
    assert sum(
        row.resolution_state in blueprint.ROBINHOOD_CURVE_BLOCKING_STATES
        for row in blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
    ) == 23


def test_aapl_seam_binds_schema_v2_but_produces_no_launch_action():
    from config import BluePrint as blueprint

    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    seam = _action(plan, "preserve-stock-extension-seam")
    assert seam["requires"] == [
        f"stock:{path}" for path in blueprint.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS
    ]
    assert len(seam["requires"]) == 16
    assert len(seam["blockers"]) == 12
    assert all(blocker.startswith("H05_STOCK_") for blocker in seam["blockers"])
    assert set(blueprint.ROBINHOOD_STOCK_RESOLVED_REPOSITORY_FACT_PATHS) == {
        "Deployment.DP-11.stock.vaultArtifact",
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
        "Deployment.DP-11.stock.m4ComposedProof",
    }
    assert all(
        action.get("artifact") != "GuardedErc20"
        and not action["semantic_action_id"].startswith(
            ("deploy-aapl", "register-aapl", "configure-aapl")
        )
        for action in _actions(plan)
    )
    assert "AAPL" not in (ROOT / "contracts/config/DefaultsRobinhood.vy").read_text()


def test_reward_product_packet_is_consumed_but_promotion_stays_blocked():
    from config import BluePrint as blueprint

    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    stage = next(item for item in plan["stages"] if item["migration_id"] == "0600")
    seam = _action(plan, "preserve-reward-promotion-seam")
    assert "B-REWARD-PROMOTION" in stage["blockers"]
    assert blueprint.ROBINHOOD_DEPLOYMENT_INPUTS[
        "Deployment.DP-15.rewards.promotion"
    ].disposition == "approved"
    assert len(seam["blockers"]) == 12
    assert all(
        blocker.startswith("H05_BINDING_REWARD_")
        for blocker in seam["blockers"]
    )
    assert "stock-rewards-disabled" in seam["postconditions"]
    assert "reward-activation-remains-operationally-blocked" in seam["postconditions"]


def test_pool_creation_is_separate_from_lp_asset_admission():
    plan = _synthetic()
    pool = _action(plan, "create-or-bind-green-usdg-pool")
    seam = _action(plan, "preserve-lp-extension-seam")
    assert pool["kind"] == "configuration"
    assert "address:GREEN_USDG_CURVE_POOL" in pool["provides"]
    assert {
        "green-usdg-lp-asset-absent",
        "ripe-weth-lp-asset-absent",
        "psm-reserves-not-liquidity-funding",
        "uniswap-accounting-absent",
    } <= set(seam["postconditions"])
    assert all(
        action.get("component_id") not in {"CM-035", "CM-036", "CM-037", "CM-050"}
        for action in _actions(plan)
        if action["kind"] in {"deployment", "registration"}
    )


def test_curve_abort_and_post_registration_recovery_are_explicit():
    plan = _synthetic()
    validate = _action(plan, "validate-direct-green-pricing")
    assert {
        "green-price-validation-failed",
        "zero-price-input",
        "stale-chainlink-input",
        "invalid-pool-input",
        "abi-incompatible-pool-input",
        "reverting-pool-input",
        "unsafe-configuration",
        "pricing-recursion-detected",
        "curve-usdg-feed-present",
    } == set(validate["abort_if"])
    for semantic_id in ("register-curve-prices", "register-blue-chip-yield-prices"):
        assert "returned-registry-id-mismatch" in _action(plan, semantic_id)["abort_if"]
    disable = _action(plan, "recover-disable-curve-id-two")
    assert disable["operation"] == "pause-then-timelocked-disable-registry-address"
    assert disable["registry"]["registry_id"] == 2
    assert disable["postconditions"] == [
        "price-desk-id-two-zero",
        "green-has-no-unsafe-fallback",
        "bluechip-id-three-preserved",
    ]
    repair = _action(plan, "recover-update-curve-id-two")
    assert repair["operation"] == "timelocked-update-registry-address"
    assert "unrelated-placeholder-impossible" in repair["postconditions"]
    assert "bluechip-id-three-preserved" in repair["postconditions"]


def test_inactive_curve_adjacent_features_have_no_launch_actions():
    plan = _synthetic()
    inactive = set(_action(plan, "assert-disabled-routes-absent")["feature_families"])
    assert inactive == {
        "curve-lp-collateral",
        "curve-lp-valuation",
        "curve-psm-authority",
        "curve-dynamic-rates",
        "teller-green-reference-snapshots",
        "endaoment-stabilization",
        "ripe-weth-lp-admission",
        "uniswap-accounting",
    }
    rendered = json.dumps(plan, sort_keys=True)
    assert "register-uniswap" not in rendered
    assert "activate-psm" not in rendered


def test_defaults_constructor_order_and_provenance_are_exact():
    constructor = _action(_synthetic(), "deploy-defaults-robinhood")["constructor"]
    assert constructor == [
        "address:CONTRIBUTOR_TEMPLATE",
        "address:TRAINING_WHEELS",
        "address:RIPE_TOKEN",
        "address:GREEN_TOKEN",
        "address:SGREEN_TOKEN",
        "address:USDG",
        "address:WETH",
        "address:STEAKHOUSE_USDG_VAULT",
    ]


def test_final_handoff_is_last_and_requires_all_postconditions():
    plan = _synthetic()
    final_stage = plan["stages"][-1]
    assert final_stage["migration_id"] == "0900"
    final = final_stage["actions"][-1]
    assert final["semantic_action_id"] == "handoff-governance-and-relinquish-deployer"
    assert final["operation"] == "irreversible-final-authority-handoff"
    assert "handoff-is-final-action" in final["postconditions"]


def test_plan_derived_expectations_cover_artifacts_topology_absence_and_handoff():
    plan = _synthetic()
    expected = expectations_from_plan(plan)
    assert expected["chain_id"] == 4663
    assert expected["profile_id"] == "robinhood-synthetic-proof"
    assert len(expected["components"]) == 37
    assert len(expected["registries"]) == 33
    artifacts = {row["component_id"]: row["artifact"] for row in expected["components"]}
    assert artifacts["CM-049"] == "DefaultsRobinhood"
    assert artifacts["CM-017"] == "CurvePrices"
    assert artifacts["CM-008"] == "Ledger"
    price_rows = [
        (row["registry_id"], row["component_id"])
        for row in expected["registries"]
        if row["domain"] == "price_desk"
    ]
    assert price_rows == [(1, "CM-016"), (2, "CM-017"), (3, "CM-018")]
    contract = expected["plan_contract"]
    assert contract["selected_components"] == sorted(
        plan["component_coverage"]["selected"]
    )
    assert contract["blocked_components"] == ["CM-008"]
    assert contract["artifact_kind"] == "synthetic-proof"
    assert contract["plan_hash"] is None
    assert contract["proof_hash"] == plan["proof_hash"]
    assert contract["action_census"] == plan["action_census"]
    assert contract["absent_components"] == sorted(
        plan["component_coverage"]["omitted"]
        + plan["component_coverage"]["deferred"]
    )
    assert contract["pricing_posture"]["priority_ids"] == [1, 3]
    assert "green-resolves-through-curve-after-priority-miss" in contract[
        "pricing_posture"
    ]["feed_postconditions"]
    assert contract["pricing_posture"]["disable_operation"] == (
        "pause-then-timelocked-disable-registry-address"
    )
    assert len(contract["aapl_posture"]["input_refs"]) == 16
    assert "reward-activation-remains-operationally-blocked" in contract[
        "reward_posture"
    ]["postconditions"]
    assert "uniswap-accounting-absent" in contract["lp_posture"][
        "postconditions"
    ]
    assert {
        "psm-can-mint-false",
        "psm-can-redeem-false",
        "psm-auto-deposit-false",
        "psm-reserve-funding-zero",
        "psm-yield-disabled",
        "psm-non-governance-lite-signers-zero",
    } == set(contract["psm_posture"])
    assert contract["role_posture"]["governance_safe_guardian_refs"] == [
        "input:Deployment.DP-18.roles.governance",
        "input:Deployment.DP-18.roles.safe",
        "input:Deployment.DP-18.roles.guardian",
    ]
    assert "only-approved-capabilities-enabled" in contract[
        "capability_posture"
    ]["postconditions"]
    assert contract["ccip_present"] is False
    assert contract["uniswap_present"] is False
    assert contract["final_authority"]["deployer_retains_authority"] is False
    assert len(contract["output_identity"]) == 64


def test_plan_expectation_contract_mismatch_fails_closed():
    expected = expectations_from_plan(_synthetic())
    observed = copy.deepcopy(expected)
    observed.pop("profile_kind")
    observed["mode"] = "synthetic"
    observed["edges"] = []
    assert assert_deployment(expected, observed).ok

    observed["plan_contract"]["pricing_posture"]["priority_ids"] = [1, 2]
    report = assert_deployment(expected, observed)
    assert {failure.code for failure in report.failures} == {
        "PLAN_EXPECTATION_MISMATCH"
    }


def test_check_deployment_prints_plan_expectations_without_rpc_or_history():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_deployment.py",
            "--print-plan-expectations",
            "robinhood-mainnet",
            "--preview",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    expected = json.loads(result.stdout)
    assert expected["profile_id"] == "robinhood-mainnet"
    assert expected["plan_contract"]["plan_hash"] is None
    assert "output_identity" in expected["plan_contract"]


def _copy_sources(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "migrations").mkdir(parents=True)
    shutil.copytree(ROOT / "migrations/robinhood", root / "migrations/robinhood")
    return root


def test_reordering_price_registrations_is_rejected(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    price = next(stage for stage in stages if stage["migration_id"] == "0400")
    actions = price["actions"]
    curve = next(i for i, action in enumerate(actions) if action["semantic_action_id"] == "register-curve-prices")
    bluechip = next(i for i, action in enumerate(actions) if action["semantic_action_id"] == "register-blue-chip-yield-prices")
    actions[curve], actions[bluechip] = actions[bluechip], actions[curve]
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(MigrationPlanError, match="H05_PRICE_REGISTRY_ORDER"):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_removing_curve_would_shift_bluechip_and_is_rejected(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    price = next(stage for stage in stages if stage["migration_id"] == "0400")
    price["actions"] = [
        action for action in price["actions"]
        if action["semantic_action_id"] not in {
            "deploy-curve-prices-unregistered",
            "register-curve-prices",
        }
    ]
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(MigrationPlanError, match="H05_CURVE_INPUT_COVERAGE"):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_duplicate_price_registration_is_rejected(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    price = next(stage for stage in stages if stage["migration_id"] == "0400")
    duplicate = copy.deepcopy(
        next(
            action for action in price["actions"]
            if action["semantic_action_id"] == "register-chainlink-prices"
        )
    )
    duplicate["semantic_action_id"] = "register-chainlink-prices-duplicate"
    price["actions"].append(duplicate)
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(MigrationPlanError, match="H05_REGISTRY_COVERAGE"):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_missing_selected_deployment_is_rejected_even_if_registration_remains(
    monkeypatch,
):
    stages = list(load_robinhood_stages(ROOT))
    price = next(stage for stage in stages if stage["migration_id"] == "0400")
    price["actions"] = [
        action
        for action in price["actions"]
        if action["semantic_action_id"] != "deploy-chainlink-prices"
    ]
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(
        MigrationPlanError, match="H05_COMPONENT_DEPLOYMENT_COVERAGE"
    ):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_duplicate_component_deployment_is_rejected(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    price = next(stage for stage in stages if stage["migration_id"] == "0400")
    duplicate = copy.deepcopy(
        next(
            action
            for action in price["actions"]
            if action["semantic_action_id"] == "deploy-chainlink-prices"
        )
    )
    duplicate["semantic_action_id"] = "deploy-chainlink-prices-duplicate"
    duplicate["provides"] = ["address:CHAINLINK_PRICES_DUPLICATE"]
    price["actions"].append(duplicate)
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(
        MigrationPlanError, match="H05_COMPONENT_DEPLOYMENT_DUPLICATE"
    ):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_deployment_artifact_cannot_drift_from_blueprint_identity(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    tokens = next(stage for stage in stages if stage["migration_id"] == "0100")
    green = next(
        action
        for action in tokens["actions"]
        if action["semantic_action_id"] == "deploy-green-token"
    )
    green["artifact"] = "RipeToken"
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(
        MigrationPlanError, match="H05_COMPONENT_ARTIFACT_MISMATCH"
    ):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_wrong_constructor_argument_count_is_rejected(monkeypatch):
    stages = list(load_robinhood_stages(ROOT))
    tokens = next(stage for stage in stages if stage["migration_id"] == "0100")
    action = next(
        action for action in tokens["actions"]
        if action["semantic_action_id"] == "deploy-defaults-robinhood"
    )
    action["constructor"].pop()
    import scripts.utils.migration_runner as runner
    monkeypatch.setattr(runner, "load_robinhood_stages", lambda *_args: tuple(stages))
    with pytest.raises(MigrationPlanError, match="H05_DEFAULTS_CONSTRUCTOR_MISMATCH"):
        build_robinhood_plan(
            "robinhood-mainnet",
            repository_root=ROOT,
            synthetic_bind_all=True,
        )


def test_migration_local_registry_id_is_rejected(tmp_path):
    root = _copy_sources(tmp_path)
    path = root / "migrations/robinhood/0400_PriceSources.py"
    text = path.read_text().replace(
        '"registry_ref": "registry:price_desk:CM-016",',
        '"registry_ref": "registry:price_desk:CM-016",\n            "registry_id": 1,',
        1,
    )
    path.write_text(text)
    with pytest.raises(MigrationPlanError, match="H05_REGISTRY_ID_LOCAL_AUTHORITY"):
        load_robinhood_stages(root)


@pytest.mark.parametrize("replacement", ("0x" + "0" * 40, "base-mainnet", "pr-66"))
def test_zero_base_and_historical_placeholder_literals_are_rejected(tmp_path, replacement):
    root = _copy_sources(tmp_path)
    path = root / "migrations/robinhood/0400_PriceSources.py"
    text = path.read_text().replace(
        '"curve:curve.address_provider"', f'"{replacement}"', 1
    )
    path.write_text(text)
    with pytest.raises(MigrationPlanError, match="H05_LOCAL_VALUE_FORBIDDEN"):
        load_robinhood_stages(root)


def _clean_committed_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "committed-repo"
    subprocess.run(
        ["/usr/bin/git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(root)],
        check=True,
    )
    changed = subprocess.run(
        [
            "/usr/bin/git",
            "ls-files",
            "--modified",
            "--deleted",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    for raw in changed:
        if not raw:
            continue
        relative = raw.decode("utf-8")
        source = ROOT / relative
        target = root / relative
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.exists():
            target.unlink()
    subprocess.run(["/usr/bin/git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "user.name=Robinhood Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
    )
    return root


def test_clean_committed_production_fixture_succeeds(tmp_path):
    root = _clean_committed_fixture(tmp_path)
    plan = build_robinhood_plan("robinhood-mainnet", repository_root=root)
    commit = subprocess.run(
        ["/usr/bin/git", "rev-parse", "HEAD^{commit}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["/usr/bin/git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    assert plan["artifact"]["kind"] == "production-plan"
    assert plan["status"] == "blocked"
    assert plan["source"]["commit"] == commit
    assert plan["source"]["tree"] == tree
    assert validate_plan_artifact(plan, repository_root=root) == plan
    preview = build_robinhood_plan(
        "robinhood-mainnet", repository_root=root, preview=True
    )
    assert preview["source"]["tree"] == plan["source"]["tree"]
    assert preview["artifact_hash"] != plan["artifact_hash"]
    with pytest.raises(
        MigrationPlanError, match="H05_EXECUTION_PRODUCTION_PLAN_REQUIRED"
    ):
        validate_execution_plan_artifact(preview, repository_root=root)
    (root / "post-plan-drift.txt").write_text("drift\n")
    with pytest.raises(
        MigrationPlanError, match="H05_PRODUCTION_REPOSITORY_DIRTY"
    ):
        validate_plan_artifact(plan, repository_root=root)


@pytest.mark.parametrize(
    "relative",
    (
        "migrations/robinhood/0100_TokensAndRipeHq.py",
        "config/BluePrint.py",
        "contracts/config/DefaultsRobinhood.vy",
        "contracts/registries/RipeHq.vy",
        "config/contract-artifact-expectations.json",
    ),
)
def test_production_rejects_modified_planning_input(tmp_path, relative):
    root = _clean_committed_fixture(tmp_path)
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(
        MigrationPlanError, match="H05_PRODUCTION_REPOSITORY_DIRTY"
    ):
        build_robinhood_plan("robinhood-mainnet", repository_root=root)


def test_production_rejects_untracked_migration_and_missing_input(tmp_path):
    root = _clean_committed_fixture(tmp_path)
    extra = root / "migrations/robinhood/0090_Unknown.py"
    extra.write_text("VALUE = 1\n")
    with pytest.raises(
        MigrationPlanError, match="H05_PRODUCTION_REPOSITORY_DIRTY"
    ):
        build_robinhood_plan("robinhood-mainnet", repository_root=root)
    extra.unlink()
    (root / "config/BluePrint.py").unlink()
    with pytest.raises(
        MigrationPlanError, match="H05_PRODUCTION_REPOSITORY_DIRTY"
    ):
        build_robinhood_plan("robinhood-mainnet", repository_root=root)


def test_preview_rejects_missing_and_symlinked_planning_inputs(tmp_path):
    root = _clean_committed_fixture(tmp_path)
    target = root / "contracts/config/DefaultsRobinhood.vy"
    replacement = root / "DefaultsRobinhood.substitute"
    replacement.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(replacement)
    with pytest.raises(
        MigrationPlanError, match="H05_PLANNING_INPUT_SYMLINK"
    ):
        build_robinhood_plan(
            "robinhood-mainnet", repository_root=root, preview=True
        )
    target.unlink()
    shutil.copy2(replacement, target)
    replacement.unlink()
    (root / "config/contract-artifact-expectations.json").unlink()
    with pytest.raises(
        MigrationPlanError, match="H05_PLANNING_INPUT_MISSING"
    ):
        build_robinhood_plan(
            "robinhood-mainnet", repository_root=root, preview=True
        )


def test_preview_identity_rejects_reported_tree_tamper_and_repository_drift(tmp_path):
    root = _clean_committed_fixture(tmp_path)
    marker = root / "candidate-note.txt"
    marker.write_text("candidate\n")
    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=root, preview=True
    )
    tampered = copy.deepcopy(plan)
    tampered["source"]["tree"] = "0" * 40
    with pytest.raises(MigrationPlanError, match="H05_PLAN_SOURCE_DRIFT"):
        validate_plan_artifact(tampered, repository_root=root)
    marker.write_text("drifted\n")
    with pytest.raises(MigrationPlanError, match="H05_PLAN_SOURCE_DRIFT"):
        validate_plan_artifact(plan, repository_root=root)


def test_synthetic_proof_is_domain_separated_and_never_history_or_execution_eligible():
    preview = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    proof = _synthetic()
    assert proof["proof_hash"] != preview["preview_hash"]
    assert proof["plan_hash"] is preview["plan_hash"] is None
    assert proof["artifact"]["executable"] is False
    assert proof["artifact"]["history_eligible"] is False
    with pytest.raises(
        MigrationPlanError, match="H05_EXECUTION_PRODUCTION_PLAN_REQUIRED"
    ):
        validate_execution_plan_artifact(proof, repository_root=ROOT)
    with pytest.raises(
        MigrationPlanError, match="H05_HISTORY_PRODUCTION_PLAN_REQUIRED"
    ):
        read_bound_h06_history(
            proof,
            profile_id="robinhood-mainnet",
            expected_chain_id=4663,
            source_commit="0" * 40,
            source_tree="0" * 40,
            history_root=ROOT / "migration_history/robinhood-mainnet/v1",
        )


def test_synthetic_proof_preserves_ledger_blocker_and_enumerates_every_override():
    proof = _synthetic()
    ledger = _action(proof, "deploy-ledger")
    assert ledger["component_authority"]["selection_state"] == "blocked"
    assert ledger["status"] == "proof-overridden"
    assert ledger["blockers"]
    overrides = {row["key"] for row in proof["synthetic_authority_overrides"]}
    assert overrides == set(proof["blockers"])
    assert set(ledger["blockers"]) <= overrides
    real = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    assert real["status"] == "blocked"
    assert real["artifact"]["kind"] == "preview-plan"
    assert real["synthetic_authority_overrides"] == []
    assert "robinhood-synthetic-proof" not in canonical_jcs_bytes(real).decode()


def test_assertion_derivation_rejects_ledger_omission_extra_action_and_census_drift():
    proof = _synthetic()
    without_ledger = copy.deepcopy(proof)
    stage = next(row for row in without_ledger["stages"] if row["migration_id"] == "0200")
    stage["actions"] = [
        action
        for action in stage["actions"]
        if action["semantic_action_id"] != "deploy-ledger"
    ]
    with pytest.raises(DeploymentAssertionInputError, match="action census"):
        expectations_from_plan(without_ledger)

    extra = copy.deepcopy(proof)
    extra["stages"][0]["actions"].append(copy.deepcopy(extra["stages"][0]["actions"][0]))
    extra["stages"][0]["actions"][-1]["action_id"] = "0010:999999:extra"
    extra["stages"][0]["actions"][-1]["semantic_action_id"] = "extra-action"
    with pytest.raises(DeploymentAssertionInputError, match="action census"):
        expectations_from_plan(extra)

    wrong_census = copy.deepcopy(proof)
    wrong_census["action_census"]["deployments"] = 36
    with pytest.raises(DeploymentAssertionInputError, match="117/37/33"):
        expectations_from_plan(wrong_census)


def test_assertion_derivation_rejects_blocked_disposition_suppression():
    proof = copy.deepcopy(_synthetic())
    ledger = _action(proof, "deploy-ledger")
    ledger["component_authority"]["selection_state"] = "selected"
    with pytest.raises(
        DeploymentAssertionInputError, match="CM-008 Ledger blocked"
    ):
        expectations_from_plan(proof)


def test_80_source_readiness_and_99_plan_blockers_cannot_drift():
    plan = build_robinhood_plan(
        "robinhood-mainnet", repository_root=ROOT, preview=True
    )
    census = {
        "binding": sum(key.startswith("H05_BINDING_") for key in plan["blockers"]),
        "curve": sum(key.startswith("H05_CURVE_") for key in plan["blockers"]),
        "external_address": sum(key.startswith("H05_EXTERNAL_") for key in plan["blockers"]),
        "deployment_input": sum(key.startswith("H05_INPUT_") for key in plan["blockers"]),
        "reservation": sum(key.startswith("B-") for key in plan["blockers"]),
        "stock": sum(key.startswith("H05_STOCK_") for key in plan["blockers"]),
    }
    assert len(plan["blockers"]) == 99
    assert census == {
        "binding": 37,
        "curve": 23,
        "external_address": 5,
        "deployment_input": 18,
        "reservation": 4,
        "stock": 12,
    }

    status = yaml.safe_load((ROOT / "docs/chains/rh/status.yaml").read_text())
    readiness = status["migration_readiness"]
    assert readiness["source_configuration"] == {
        "blockers": 80,
        "configuration_consistent": True,
        "deployment_ready": False,
    }
    assert readiness["executable_plan"] == {
        "blockers": 99,
        "categories": census,
    }
    assert "Neither count replaces the other" in readiness["relationship"]

    for relative in (
        "docs/chains/rh/deployment-owner-quickstart.md",
        "docs/chains/rh/robinhood-deployment-validation-plan.md",
    ):
        text = (ROOT / relative).read_text()
        for phrase in (
            "80",
            "99",
            "37",
            "23",
            "5 external",
            "18 deployment",
            "4 stage" if relative.endswith("quickstart.md") else "4 reservation",
            "12 Stock",
            "neither count replaces the other",
        ):
            assert phrase in text
