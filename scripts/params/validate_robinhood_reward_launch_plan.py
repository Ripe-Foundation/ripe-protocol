#!/usr/bin/env python3
"""Fail-closed validation for the approved Robinhood reward product decision.

The packet binds the exact approved PR #66 product values and accepted
shared-budget risks.  It grants no deployment, activation, or release authority.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "config" / "robinhood-reward-launch-plan.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import BluePrint as source_blueprint  # noqa: E402
from scripts.params import generate_robinhood_defaults as defaults_sync  # noqa: E402


class RewardPlanError(ValueError):
    pass


SOURCE_PREDICATES = {
    "contracts/modules/TimeLock.vy": (
        "confirmBlock: uint256 = block.number + self.actionTimeLock",
        "self.pendingActions[_actionId] = empty(PendingAction)",
        "def getActionConfirmationBlock(_actionId: uint256) -> uint256:",
    ),
    "contracts/config/SwitchboardCharlie.vy": (
        "def _hasPermsForLiteAction(_caller: address, _hasLiteAccess: bool) -> bool:",
        "if _hasLiteAccess:",
        "def pause(_contractAddr: address, _shouldPause: bool) -> bool:",
        "assert self._hasPermsForLiteAction(msg.sender, _shouldPause)",
    ),
    "contracts/config/SwitchboardAlpha.vy": (
        "def setCanClaimLoot(_shouldEnable: bool, _missionControl: address = empty(address)) -> bool:",
        "def setCanClaimInStabPool(_shouldEnable: bool, _missionControl: address = empty(address)) -> bool:",
        "def setRewardsPointsEnabled(_shouldEnable: bool, _missionControl: address = empty(address)) -> bool:",
        "def setRipePerBlock(_ripePerBlock: uint256, _missionControl: address = empty(address)) -> uint256:",
        "def setAutoStakeParams(_autoStakeRatio: uint256, _autoStakeDurationRatio: uint256, _stabPoolRipePerDollarClaimed: uint256, _missionControl: address = empty(address)) -> uint256:",
        "assert gov._canGovern(msg.sender) # dev: no perms",
        "confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)",
    ),
    "contracts/registries/RipeHq.vy": (
        "def setMintingEnabled(_shouldEnable: bool):",
        "assert msg.sender == gov.governance # dev: no perms",
        "if not self.mintEnabled:",
    ),
    "contracts/core/Lootbox.vy": (
        "if rewards.lastUpdate != 0 and block.number > rewards.lastUpdate:",
        "rewards.lastUpdate = block.number",
        "if elapsedBlocks == 0 or _config.ripePerBlock == 0 or b.ripeAvailForRewards == 0:",
        "newRipeDistro: uint256 = min(elapsedBlocks * _config.ripePerBlock, b.ripeAvailForRewards)",
        "if not _arePointsEnabled or elapsedBlocks == 0:",
    ),
    "contracts/data/Ledger.vy": (
        "self.ripeAvailForRewards -= min(self.ripeAvailForRewards, _ripeRewards.newRipeRewards)",
        "self.ripeAvailForRewards -= _amount",
    ),
    "contracts/vaults/modules/StabVault.vy": (
        "ripeAvailable: uint256 = min(ripeClaimRewards, staticcall Ledger(_a.ledger).ripeAvailForRewards())",
    ),
}


def _check_source_predicates() -> None:
    for relative, predicates in SOURCE_PREDICATES.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for predicate in predicates:
            if predicate not in source:
                raise RewardPlanError(f"REWARD_PLAN_SOURCE_DRIFT:{relative}:{predicate}")


def _value(defaults: dict[str, Any], path: str) -> Any:
    try:
        return defaults[path]["raw"]
    except (KeyError, TypeError) as error:
        raise RewardPlanError(f"REWARD_PLAN_DEFAULT_MISSING:{path}") from error


def _candidate_values(defaults: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "arePointsEnabled": "Defaults.rewardsConfig.arePointsEnabled",
        "ripeAvailForRewards": "Defaults.ripeAvailForRewards",
        "ripePerBlock": "Defaults.rewardsConfig.ripePerBlock",
        "borrowersAlloc": "Defaults.rewardsConfig.borrowersAlloc",
        "stakersAlloc": "Defaults.rewardsConfig.stakersAlloc",
        "votersAlloc": "Defaults.rewardsConfig.votersAlloc",
        "genDepositorsAlloc": "Defaults.rewardsConfig.genDepositorsAlloc",
        "autoStakeRatio": "Defaults.rewardsConfig.autoStakeRatio",
        "autoStakeDurationRatio": "Defaults.rewardsConfig.autoStakeDurationRatio",
        "stabPoolRipePerDollarClaimed": "Defaults.rewardsConfig.stabPoolRipePerDollarClaimed",
    }
    return {
        name: {"source": path, "value": _value(defaults, path)}
        for name, path in paths.items()
    }


def _derived(values: dict[str, Any]) -> dict[str, Any]:
    raw = {name: item["value"] for name, item in values.items()}
    blocks_per_minute = source_blueprint.ROBINHOOD_CHAIN["blocks_per_minute"]
    seconds_per_block = source_blueprint.ROBINHOOD_CHAIN["evm_block_number_seconds"]
    blocks_per_day = blocks_per_minute * 60 * 24
    rate = Decimal(raw["ripePerBlock"]) / Decimal(10**18)
    budget = Decimal(raw["ripeAvailForRewards"]) / Decimal(10**18)
    with localcontext() as context:
        context.prec = 60
        continuous_days = budget / rate / Decimal(blocks_per_day)
        max_rate_30d = budget / Decimal(blocks_per_day * 30)
    first_capped_increment = (
        raw["ripeAvailForRewards"] + raw["ripePerBlock"] - 1
    ) // raw["ripePerBlock"]
    min_lock = _value(
        defaults_sync.extract_defaults_values(),
        "Defaults.ripeGovVaultConfigs[RIPE].config.lockTerms.minLockDuration",
    )
    max_lock = _value(
        defaults_sync.extract_defaults_values(),
        "Defaults.ripeGovVaultConfigs[RIPE].config.lockTerms.maxLockDuration",
    )
    lock_blocks = (
        (max_lock - min_lock) * raw["autoStakeDurationRatio"] // 10_000
    )
    return {
        "classification": "derived_from_candidate_values_and_blueprint_cadence",
        "blocks_per_minute": blocks_per_minute,
        "seconds_per_block": seconds_per_block,
        "allocation_sum_bps": sum(
            raw[name]
            for name in (
                "borrowersAlloc",
                "stakersAlloc",
                "votersAlloc",
                "genDepositorsAlloc",
            )
        ),
        "ripe_per_day": str(rate * blocks_per_day),
        "borrower_ripe_per_day": str(
            rate * blocks_per_day * raw["borrowersAlloc"] / 10_000
        ),
        "staker_ripe_per_day": str(
            rate * blocks_per_day * raw["stakersAlloc"] / 10_000
        ),
        "emission_only_continuous_budget_days": str(continuous_days),
        "emission_only_first_capped_block_increment": first_capped_increment,
        "emission_only_first_capped_wall_seconds": first_capped_increment * seconds_per_block,
        "emission_only_first_capped_wall_time": "15d10h22m24s",
        "shared_budget_theoretical_minimum_runway_seconds": 0,
        "thirty_day_emission_budget_ripe": "1944.000",
        "thirty_day_minimum_budget_ripe_before_stability_reserve": "1944",
        "thirty_day_max_rate_ripe_per_block_before_stability_reserve": str(max_rate_30d),
        "stability_reserve": "none_selected_owner_accepted",
        "auto_stake_lock_blocks": lock_blocks,
        "auto_stake_lock_days": str(
            Decimal(lock_blocks) * seconds_per_block / Decimal(86_400)
        ),
    }


@lru_cache(maxsize=1)
def expected_plan() -> dict[str, Any]:
    _check_source_predicates()
    defaults = defaults_sync.extract_defaults_values()
    values = _candidate_values(defaults)
    alpha_delay = source_blueprint.ROBINHOOD_DEPLOYMENT_INPUTS[
        "Deployment.DP-05.timelocks.SwitchboardAlpha.minTimeLock"
    ].value
    if alpha_delay != 600:
        raise RewardPlanError("REWARD_PLAN_ALPHA_DELAY_DRIFT")

    return {
        "schema": "ripe.robinhood.reward-launch-owner-decision-packet.v3",
        "packet": {
            "classification": "owner_approved_product_decision_operationally_blocked",
            "is_configuration_authority": False,
            "value_authorities": [
                "contracts/config/DefaultsRobinhood.vy",
                "config/BluePrint.py",
            ],
            "identity_algorithm": "sha256(file_bytes)",
            "identity_effect": "approved_product_decision_binding_no_lifecycle_authority",
            "owner_acceptance": "approved",
            "dp15_state": "approved_concrete_packet_hash",
            "p_h04_399_state": "approved",
            "execution_authorized": False,
            "deployment_authorized": False,
            "activation_authorized": False,
            "rpc_authorized": False,
        },
        "owner_product_decision": {
            "scope": "exact_pr66_initial_launch_reward_configuration",
            "accepted_shared_budget": "Lootbox_emissions_and_Stability_rewards_share_the_1000_RIPE_budget",
            "emission_only_runway_days_approx": "15.432",
            "stability_claim_effect": "can_shorten_emission_only_runway",
            "shared_budget_theoretical_minimum_runway_seconds": 0,
            "dedicated_stability_reserve": "none_selected",
            "separate_stability_budget": "none_selected",
            "stability_redesign": "not_selected",
            "stability_launch_disablement": "not_selected",
            "shared_budget_risks_accepted": True,
            "lifecycle_authority_effect": "none",
        },
        "candidate_configuration": {
            "classification": "derived_owner_approved_launch_values",
            "configuration_timing": "configured_during_deployment",
            "emission_start": "after_first_successful_global_lootbox_checkpoint",
            "values": values,
        },
        "derived_calculations": _derived(values),
        "runtime_facts": [
            {
                "id": "RF-01",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/core/Lootbox.vy:_getLatestGlobalRipeRewards",
                "fact": "when lastUpdate is zero, the first successful global update sets lastUpdate and distributes zero",
            },
            {
                "id": "RF-02",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/core/Lootbox.vy:_getLatestGlobalRipeRewards",
                "fact": "accrual begins only after that checkpoint and a later update recognizes elapsed blocks at the rate current when the later update executes",
            },
            {
                "id": "RF-03",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/core/Lootbox.vy and contracts/data/Ledger.vy",
                "fact": "global emission and Stability claims consume the same Ledger ripeAvailForRewards budget; budget exhaustion yields zero new emission or claim rewards",
            },
            {
                "id": "RF-04",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/core/Lootbox.vy pause gate and lazy checkpoint",
                "fact": "pausing Lootbox freezes accounting calls but not the configured rate; unpausing before zero is confirmed allows the next update to backfill the paused interval",
            },
            {
                "id": "RF-05",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/core/Lootbox.vy point checkpoint helpers",
                "fact": "stored points survive disable; a disabled-state checkpoint advances lastUpdate and skips the disabled interval, while re-enable before that checkpoint can recognize the uncheckpointed interval",
            },
            {
                "id": "RF-06",
                "classification": "source_validated_contract_fact",
                "evidence": "contracts/registries/RipeHq.vy:setMintingEnabled",
                "fact": "the global mint breaker is governance-only and immediate, blocks both GREEN and RIPE mint permission, and does not erase accrued accounting",
            },
            {
                "id": "RF-07",
                "classification": "derived_scope_limit",
                "evidence": "derived_calculations and RF-03",
                "fact": "15d10h22m24s is only the emission-only maximum from the first checkpoint; shared-budget theoretical minimum runway is zero",
            },
        ],
        "emergency_runbook": {
            "classification": "source_validated_procedure_pending_operational_acceptance_and_identity_binding",
            "automatic_execution": False,
            "steps": [
                {
                    "order": 1,
                    "action": "SwitchboardCharlie.pause(Lootbox, true)",
                    "authority": "governance_or_already_qualified_lite_signer",
                    "timing": "immediate",
                    "checkpoint": "verify Lootbox paused; only governance may later unpause",
                },
                {
                    "order": 2,
                    "action": "SwitchboardAlpha.setCanClaimLoot(false)",
                    "authority": "governance_or_already_qualified_lite_signer",
                    "timing": "immediate_after_order_1",
                    "checkpoint": "verify canClaimLoot false",
                },
                {
                    "order": 3,
                    "action": "SwitchboardAlpha.setCanClaimInStabPool(false)",
                    "authority": "governance_or_already_qualified_lite_signer",
                    "timing": "immediate_after_order_2",
                    "checkpoint": "verify canClaimInStabPool false; this remains separate from Lootbox claims",
                },
                {
                    "order": 4,
                    "action": "SwitchboardAlpha.setRewardsPointsEnabled(false)",
                    "authority": "governance_or_already_qualified_lite_signer",
                    "timing": "immediate_after_order_3",
                    "checkpoint": "verify points disabled; stored points remain",
                },
                {
                    "order": 5,
                    "action": "SwitchboardAlpha.setRipePerBlock(0)",
                    "authority": "governance_only",
                    "timing": "timelocked",
                    "checkpoint": "record returned actionId and emitted/read confirmationBlock; require confirmationBlock minus initiation block at least 600",
                    "binding": "ripe_rate_action_id_and_confirmation_block_pending_runtime",
                },
                {
                    "order": 6,
                    "action": "SwitchboardAlpha.setAutoStakeParams(currentAutoStakeRatio, currentAutoStakeDurationRatio, 0)",
                    "authority": "governance_only",
                    "timing": "timelocked",
                    "checkpoint": "read and preserve both current ratios; record distinct returned actionId and confirmationBlock; require at least 600 blocks",
                    "binding": "stability_rate_action_id_and_confirmation_block_pending_runtime",
                },
                {
                    "order": 7,
                    "action": "wait_until_both_confirmation_blocks",
                    "authority": "observation_only",
                    "timing": "minimum_600_post_setup_blocks_per_action",
                    "checkpoint": "Lootbox stays paused and both claim flags plus points stay disabled; early execution must fail",
                },
                {
                    "order": 8,
                    "action": "SwitchboardAlpha.executePendingAction(ripeRateActionId) and executePendingAction(stabilityRateActionId)",
                    "authority": "governance_only",
                    "timing": "at_or_after_each_recorded_confirmation_block_before_expiration",
                    "checkpoint": "verify both pending actions cleared, ripePerBlock zero, Stability rate zero, and both auto-stake ratios unchanged; keep Lootbox paused",
                },
                {
                    "order": 9,
                    "action": "RipeHq.setMintingEnabled(false)",
                    "authority": "governance_only",
                    "timing": "immediate_last_resort_only",
                    "checkpoint": "verify global GREEN and RIPE mint permissions disabled; do not represent this as reward-accounting rollback",
                },
            ],
            "last_resort_is_not_default_step": True,
            "containment_end_state": "Lootbox_paused_claims_disabled_points_disabled_both_reward_rates_zero",
        },
        "re_enable_conditions": {
            "classification": "operational_prerequisites_no_automatic_reversal",
            "required_before_any_re_enable": [
                "incident resolved and written owner acceptance recorded",
                "approved reward configuration and shared-budget risk acceptance revalidated if bytes change",
                "governance and any lite signer identities verified without inventing bindings",
                "monitoring owners thresholds alerts and zero-budget response accepted",
                "both zero actions confirmed and onchain values independently verified",
                "fresh restart action IDs and confirmation blocks recorded for any nonzero rates",
            ],
            "checkpoint_order": [
                "keep Lootbox paused and both claim flags disabled while restart actions wait",
                "at confirmed zero, governance unpauses Lootbox",
                "an explicitly bound registered RIPE contract caller performs a zero-rate global update to advance lastUpdate without distributing the paused interval",
                "immediately verify zero distribution and unchanged remaining budget, then checkpoint points while disabled where the affected point paths require it",
                "before a nonzero rate becomes effective, perform the final zero-rate checkpoint; execute the owner-approved rate action only after that checkpoint",
                "enable points and Lootbox claims only after configuration and checkpoint verification",
                "enable Stability claims only after the approved shared-budget policy and all operational claim-gate prerequisites are verified",
            ],
            "unbound_registered_ripe_checkpoint_caller": "pending_owner_binding",
        },
        "remaining_operational_prerequisites": [
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
        ],
        "operational_blockers": [
            "B-REWARD-PROMOTION",
            "B-H05-PLAN",
            "B-SECOPS-HANDOFF",
            "B-H08-PROOF",
            "B-H09-RELEASE",
        ],
    }


def validate_plan(plan: dict[str, Any]) -> None:
    expected = expected_plan()
    if plan != expected:
        raise RewardPlanError("REWARD_PLAN_SEMANTIC_DRIFT")


def validate_path(path: Path = PLAN_PATH) -> str:
    raw = path.read_bytes()
    try:
        plan = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RewardPlanError("REWARD_PLAN_INVALID_JSON") from error
    if not isinstance(plan, dict):
        raise RewardPlanError("REWARD_PLAN_NOT_OBJECT")
    validate_plan(plan)
    canonical = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    if raw != canonical.encode("utf-8"):
        raise RewardPlanError("REWARD_PLAN_NONCANONICAL_BYTES")
    digest = hashlib.sha256(raw).hexdigest()
    promotion = source_blueprint.ROBINHOOD_DEPLOYMENT_INPUTS[
        "Deployment.DP-15.rewards.promotion"
    ]
    if promotion.disposition != "approved" or promotion.value != digest:
        raise RewardPlanError("REWARD_PLAN_DP15_BINDING_DRIFT")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.render:
        print(json.dumps(expected_plan(), indent=2, ensure_ascii=False))
        return 0
    digest = validate_path(args.plan)
    print(f"REWARD_PLAN_OK sha256={digest} owner_acceptance=approved dp15=approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
