from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from config.BluePrint import ROBINHOOD_DEPLOYMENT_INPUTS
from config.robinhood_blueprint import ROBINHOOD_BLUEPRINT
from scripts.params import generate_robinhood_defaults as defaults_sync
from scripts.params.validate_robinhood_reward_launch_plan import (
    RewardPlanError,
    validate_path,
    validate_plan,
)


pytestmark = pytest.mark.release


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep reward-plan checks independent of protocol deployment."""


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "config" / "robinhood-reward-launch-plan.json"
LEDGER = ROOT / "config" / "robinhood-parameters.json"
PLAN_SHA256 = "f84bb5558c3bcce6eb5018e723a42f7270eae63ed8f23789b47ee99663d51234"


def _ledger_record(record_id: str) -> dict:
    ledger = json.loads(LEDGER.read_bytes())
    return next(row for row in ledger["parameters"] if row["id"] == record_id)


def _leaf_paths(value, prefix=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _leaf_paths(child, prefix + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _leaf_paths(child, prefix + (index,))
    else:
        yield prefix


def _mutated(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if value is None:
        return "mutated"
    return f"{value}:mutated"


def _mutate_at(value, path):
    cursor = value
    for segment in path[:-1]:
        cursor = cursor[segment]
    cursor[path[-1]] = _mutated(cursor[path[-1]])


def test_approved_reward_packet_validates_without_lifecycle_authority():
    plan_bytes = PLAN.read_bytes()
    plan = json.loads(plan_bytes)
    assert validate_path(PLAN) == PLAN_SHA256
    assert hashlib.sha256(plan_bytes).hexdigest() == PLAN_SHA256
    assert plan["packet"]["identity_effect"] == "approved_product_decision_binding_no_lifecycle_authority"
    assert plan["packet"]["owner_acceptance"] == "approved"
    assert plan["packet"]["is_configuration_authority"] is False
    assert plan["packet"]["deployment_authorized"] is False
    assert plan["packet"]["activation_authorized"] is False


def test_every_packet_leaf_is_fail_closed_against_semantic_mutation():
    plan = json.loads(PLAN.read_bytes())
    paths = tuple(_leaf_paths(plan))
    assert len(paths) >= 100
    for path in paths:
        candidate = copy.deepcopy(plan)
        _mutate_at(candidate, path)
        with pytest.raises(RewardPlanError, match="REWARD_PLAN_SEMANTIC_DRIFT"):
            validate_plan(candidate)


def test_dp15_and_p_h04_399_are_approved_while_reward_operations_remain_blocked():
    dp15 = ROBINHOOD_DEPLOYMENT_INPUTS["Deployment.DP-15.rewards.promotion"]
    assert dp15.disposition == "approved"
    assert dp15.value == PLAN_SHA256

    record = _ledger_record("P-H04-399")
    assert record["status"] == "approved"
    assert record["approval"]["status"] == "approved"
    assert record["blockers"] == []
    assert record["value"] == {
        "kind": "concrete",
        "raw": PLAN_SHA256,
    }

    blockers = {item.blocker_id for item in ROBINHOOD_BLUEPRINT.blockers}
    assert "B-REWARD-PROMOTION" in blockers
    assert len(blockers) == 28
    ready, readiness_blockers = defaults_sync.deployment_readiness()
    assert ready is False
    assert len(readiness_blockers) == 65
    assert not any("Deployment.DP-15.rewards.promotion" in item for item in readiness_blockers)


def test_runway_and_shared_budget_risks_are_explicitly_owner_accepted():
    plan = json.loads(PLAN.read_bytes())
    derived = plan["derived_calculations"]
    assert derived["emission_only_first_capped_wall_time"] == "15432d2h22m24s"
    assert derived["shared_budget_theoretical_minimum_runway_seconds"] == 0
    assert derived["thirty_day_minimum_budget_ripe_before_stability_reserve"] == "1944"
    assert derived["thirty_day_max_rate_ripe_per_block_before_stability_reserve"].startswith(
        "4.629629629629"
    )
    assert derived["stability_reserve"] == "none_selected_owner_accepted"
    decision = plan["owner_product_decision"]
    assert decision["emission_only_runway_days_approx"] == "15432.099"
    assert decision["stability_claim_effect"] == "can_shorten_emission_only_runway"
    assert decision["shared_budget_theoretical_minimum_runway_seconds"] == 0
    assert decision["dedicated_stability_reserve"] == "none_selected"
    assert decision["separate_stability_budget"] == "none_selected"
    assert decision["stability_redesign"] == "not_selected"
    assert decision["stability_launch_disablement"] == "not_selected"
    assert decision["shared_budget_risks_accepted"] is True
    assert set(plan["remaining_operational_prerequisites"]) == {
        "initial_global_and_points_checkpoint_procedure",
        "exact_governance_identity",
        "qualified_lite_signer_identity_if_used",
        "registered_ripe_checkpoint_caller_identity",
        "emergency_runbook_operational_acceptance",
        "monitoring_owners_thresholds_alert_routes_and_zero_budget_response",
        "h05_deterministic_plan",
        "h08_post_deployment_assertions",
        "h09_fork_qualification",
        "h06_operator_binding",
        "testnet_rehearsal",
        "release_authorization",
    }


def test_emergency_order_binds_exact_actions_authorities_and_600_block_delay():
    plan = json.loads(PLAN.read_bytes())
    steps = plan["emergency_runbook"]["steps"]
    assert [step["order"] for step in steps] == list(range(1, 10))
    assert steps[0]["action"] == "SwitchboardCharlie.pause(Lootbox, true)"
    assert steps[1]["action"] == "SwitchboardAlpha.setCanClaimLoot(false)"
    assert steps[2]["action"] == "SwitchboardAlpha.setCanClaimInStabPool(false)"
    assert steps[3]["action"] == "SwitchboardAlpha.setRewardsPointsEnabled(false)"
    assert steps[4]["authority"] == steps[5]["authority"] == "governance_only"
    assert steps[6]["timing"] == "minimum_600_post_setup_blocks_per_action"
    assert "keep Lootbox paused" in steps[7]["checkpoint"]
    assert steps[8]["action"] == "RipeHq.setMintingEnabled(false)"
    assert plan["emergency_runbook"]["last_resort_is_not_default_step"] is True
