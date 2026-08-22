#!/usr/bin/env python3
"""Fail-closed qualification for Instant Bond Lane activation inputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "instant-bond-lane-activation.json"
EXPECTED_SWITCHBOARDS = tuple(
    f"Switchboard{name}" for name in ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot")
)
LANE_MUTATORS = (
    "setConfig",
    "setCanBuyNow",
    "setRateOverride",
    "cancelRateOverride",
)
EXPECTED_LANE_REACHABILITY = {
    name: list(LANE_MUTATORS) if name == "SwitchboardFoxtrot" else []
    for name in EXPECTED_SWITCHBOARDS
}
FOXTROT_SEMANTIC_METHODS = (
    "setInstantBondConfig",
    "setCanBuyNow",
    "setInstantBondRateOverride",
    "cancelInstantBondRateOverride",
    "executePendingAction",
    "cancelPendingAction",
)
ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH_PATTERN = re.compile(r"^(0x)?[0-9a-fA-F]{64}$")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def static_switchboard_errors(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    paths = sorted((root / "contracts" / "config").glob("Switchboard*.vy"))
    discovered = tuple(path.stem for path in paths)
    if discovered != EXPECTED_SWITCHBOARDS:
        errors.append(
            f"switchboard source inventory changed: expected {EXPECTED_SWITCHBOARDS}, got {discovered}"
        )
    configured = tuple(manifest["switchboard_authority"]["source_inventory"])
    if configured != EXPECTED_SWITCHBOARDS:
        errors.append("manifest switchboard source inventory is not canonical")

    for path in paths:
        source = path.read_text()
        if "raw_call(" in source or "method_id(" in source:
            errors.append(f"generic execution primitive requires review: {path.relative_to(root)}")
    foxtrot = (root / "contracts" / "config" / "SwitchboardFoxtrot.vy").read_text()
    for method in FOXTROT_SEMANTIC_METHODS:
        if f"def {method}(" not in foxtrot:
            errors.append(f"Foxtrot semantic method missing: {method}")
    lane = (root / "contracts" / "core" / "InstantBondLane.vy").read_text()
    for method in LANE_MUTATORS:
        if f"def {method}(" not in lane:
            errors.append(f"Lane mutator missing: {method}")
    return errors


def draft_errors(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors = static_switchboard_errors(root, manifest)
    if manifest.get("schema") != "ripe.instant-bond-lane.activation.v1":
        errors.append("unexpected activation schema")
    if not manifest.get("owner_decision_url", "").startswith("https://github.com/"):
        errors.append("owner decision evidence URL is missing")
    limits = manifest.get("runtime_limits", {})
    if limits != {"eip170": 24_576}:
        errors.append("runtime limits must be EIP-170 only")
    if manifest.get("lock_bonus", {}).get("maximum_bps") != 0:
        errors.append("lock bonuses must remain disabled")
    pricing = manifest.get("pricing", {})
    if not pricing.get("snapshot_only_mid_epoch"):
        errors.append("mid-epoch pricing must remain snapshot-only")
    if pricing.get("emergency_control") != "pause_or_disable":
        errors.append("emergency control must be pause_or_disable")
    if not pricing.get("timing_is_strategically_selectable"):
        errors.append("strategic timing assumption must be explicit")
    issuance = manifest.get("issuance", {})
    if issuance.get("mint_budget_scope") != "per_lane_instance":
        errors.append("mint budget scope must be per_lane_instance")
    purchase = manifest.get("purchase_execution", {})
    if not purchase.get("full_fill_only"):
        errors.append("purchase execution must remain full-fill-only")
    override = manifest.get("rate_override", {})
    if override.get("lifetime") != "until_consumed":
        errors.append("override lifetime must remain until_consumed")
    if not override.get("revalidation_or_cancellation_required_before_reopen"):
        errors.append("override reopen revalidation control is missing")
    authority = manifest.get("switchboard_authority", {})
    if authority.get("model") != "all_registered_switchboards":
        errors.append("switchboard authority model changed")
    if authority.get("intended_semantic_entrypoint") != "SwitchboardFoxtrot":
        errors.append("Foxtrot semantic entrypoint is not pinned")
    if manifest.get("constructor", {}).get("proxy_permitted"):
        errors.append("proxy deployment is not approved by the dated owner decision")
    if manifest.get("activation_approved"):
        errors.append("draft manifest must not self-authorize activation")
    return errors


def constructor_errors(
    constructor: dict[str, Any],
    *,
    current_block: int,
) -> list[str]:
    errors: list[str] = []
    required = {
        "ripe_hq",
        "payment_token",
        "payment_decimals",
        "genesis_block",
        "epoch_length",
        "approved_max_epoch_length",
        "approved_max_genesis_lead_blocks",
        "post_deploy_immutables_verified",
        "observed_immutables",
        "deployed_lane",
        "deployed_foxtrot",
        "lane_code_hash",
        "foxtrot_code_hash",
        "proxy_permitted",
        "proxy_implementation_code_hash",
    }
    if set(constructor) != required:
        return ["constructor configuration must use the exact named fields"]
    for key in ("ripe_hq", "payment_token", "deployed_lane", "deployed_foxtrot"):
        if not ADDRESS_PATTERN.fullmatch(str(constructor[key])):
            errors.append(f"constructor {key} is not an address")
    payment_decimals = constructor["payment_decimals"]
    valid_payment_decimals = isinstance(payment_decimals, int) and (
        0 <= payment_decimals <= 73
    )
    if not valid_payment_decimals:
        errors.append("constructor payment_decimals is invalid")
    epoch_length = constructor["epoch_length"]
    max_epoch = constructor["approved_max_epoch_length"]
    genesis = constructor["genesis_block"]
    max_lead = constructor["approved_max_genesis_lead_blocks"]
    if not isinstance(epoch_length, int) or epoch_length <= 0:
        errors.append("epoch_length must be positive")
    elif not isinstance(max_epoch, int) or max_epoch <= 0 or epoch_length > max_epoch:
        errors.append("epoch_length exceeds the owner-approved maximum")
    if not isinstance(genesis, int) or genesis < 0:
        errors.append("genesis_block must be nonnegative")
    elif not isinstance(max_lead, int) or max_lead < 0 or genesis > current_block + max_lead:
        errors.append("genesis_block exceeds the owner-approved future lead")
    if not constructor["post_deploy_immutables_verified"]:
        errors.append("post-deploy immutable assertions have not passed")
    observed = constructor["observed_immutables"]
    expected_observed_fields = {
        "lane_ripe_hq",
        "lane_payment_token",
        "lane_genesis_block",
        "lane_epoch_length",
        "lane_payment_decimals",
        "lane_payment_scale",
        "foxtrot_lane",
    }
    if not isinstance(observed, dict) or set(observed) != expected_observed_fields:
        errors.append("observed immutables must use the exact named fields")
    else:
        expected_values = {
            "lane_ripe_hq": constructor["ripe_hq"],
            "lane_payment_token": constructor["payment_token"],
            "lane_genesis_block": constructor["genesis_block"],
            "lane_epoch_length": constructor["epoch_length"],
            "lane_payment_decimals": payment_decimals,
            "lane_payment_scale": 10**payment_decimals
            if valid_payment_decimals
            else None,
            "foxtrot_lane": constructor["deployed_lane"],
        }
        for key, expected in expected_values.items():
            if observed[key] != expected:
                errors.append(f"observed immutable mismatch: {key}")
    for key in ("lane_code_hash", "foxtrot_code_hash"):
        if not HASH_PATTERN.fullmatch(str(constructor[key])):
            errors.append(f"constructor {key} is not a code hash")
    if constructor["proxy_permitted"]:
        if not HASH_PATTERN.fullmatch(str(constructor["proxy_implementation_code_hash"])):
            errors.append("proxy implementation code hash is missing")
    elif constructor["proxy_implementation_code_hash"]:
        errors.append("proxy implementation hash is set while proxies are forbidden")
    return errors


def readiness_errors(
    manifest: dict[str, Any],
    *,
    current_block: int,
    root: Path = ROOT,
) -> list[str]:
    errors = draft_errors(manifest, root)
    pricing = manifest["pricing"]
    for key in (
        "calibration_owner",
        "calibration_artifact_sha256",
        "approved_min_up_bps",
        "approved_max_up_bps",
        "maximum_acceptable_late_sellout_catch_up_epochs",
    ):
        if not _present(pricing[key]):
            errors.append(f"pricing.{key} is missing")
    if not pricing["calibration_approved"]:
        errors.append("pricing calibration is not approved")

    issuance = manifest["issuance"]
    for key in (
        "approved_program_budget",
        "proposed_lane_mint_budget",
        "aggregate_ledger_owner",
        "aggregate_ledger_sha256",
    ):
        if not _present(issuance[key]):
            errors.append(f"issuance.{key} is missing")
    if issuance["deployment_kind"] not in ("initial", "replacement"):
        errors.append("issuance.deployment_kind must be initial or replacement")
    prior_total = 0
    for entry in issuance["prior_lane_issuance"]:
        if set(entry) != {"lane", "cumulative_minted", "retired_block"}:
            errors.append("prior Lane issuance entry has unexpected fields")
            continue
        if not ADDRESS_PATTERN.fullmatch(str(entry["lane"])):
            errors.append("prior Lane issuance address is invalid")
        if not isinstance(entry["cumulative_minted"], int) or entry["cumulative_minted"] < 0:
            errors.append("prior Lane cumulative_minted is invalid")
        else:
            prior_total += entry["cumulative_minted"]
        if not isinstance(entry["retired_block"], int) or entry["retired_block"] < 0:
            errors.append("prior Lane retired_block is invalid")
    if issuance["deployment_kind"] == "replacement" and not issuance["prior_lane_issuance"]:
        errors.append("replacement activation is missing retired Lane issuance")
    if issuance["deployment_kind"] == "initial" and issuance["prior_lane_issuance"]:
        errors.append("initial activation unexpectedly includes retired Lane issuance")
    approved_budget = issuance["approved_program_budget"]
    proposed_budget = issuance["proposed_lane_mint_budget"]
    if isinstance(approved_budget, int) and isinstance(proposed_budget, int):
        if approved_budget <= 0 or proposed_budget <= 0:
            errors.append("issuance budgets must be positive")
        elif prior_total + proposed_budget > approved_budget:
            errors.append("replacement Lane would exceed aggregate program budget")

    payment = manifest["payment_token"]
    for key in (
        "chain_id",
        "address",
        "decimals",
        "code_hash",
        "qualification_owner",
        "qualification_evidence_url",
        "price_source",
        "deviation_threshold_bps",
        "confirmation_duration_seconds",
        "monitoring_owner",
        "pause_authority",
        "pause_procedure_url",
        "reopening_requirements_url",
    ):
        if not _present(payment[key]):
            errors.append(f"payment_token.{key} is missing")
    if payment["callbacks_supported"]:
        errors.append("callback-capable payment tokens are not qualified")
    if _present(payment["address"]) and not ADDRESS_PATTERN.fullmatch(payment["address"]):
        errors.append("payment token address is invalid")
    if _present(payment["code_hash"]) and not HASH_PATTERN.fullmatch(payment["code_hash"]):
        errors.append("payment token code hash is invalid")
    if _present(payment["chain_id"]) and (
        not isinstance(payment["chain_id"], int) or payment["chain_id"] <= 0
    ):
        errors.append("payment token chain_id is invalid")
    if _present(payment["decimals"]) and (
        not isinstance(payment["decimals"], int) or not 0 <= payment["decimals"] <= 73
    ):
        errors.append("payment token decimals are invalid")
    if _present(payment["deviation_threshold_bps"]) and (
        not isinstance(payment["deviation_threshold_bps"], int)
        or not 0 < payment["deviation_threshold_bps"] <= 10_000
    ):
        errors.append("payment token deviation threshold is invalid")
    if _present(payment["confirmation_duration_seconds"]) and (
        not isinstance(payment["confirmation_duration_seconds"], int)
        or payment["confirmation_duration_seconds"] <= 0
    ):
        errors.append("payment token confirmation duration is invalid")
    constructor = manifest["constructor"]
    if _present(payment["address"]) and payment["address"] != constructor["payment_token"]:
        errors.append("qualified payment token differs from constructor input")
    if _present(payment["decimals"]) and payment["decimals"] != constructor["payment_decimals"]:
        errors.append("qualified payment decimals differ from constructor input")

    if not _present(manifest["purchase_execution"]["client_retry_guidance_url"]):
        errors.append("full-fill retry guidance is missing")
    if not _present(manifest["rate_override"]["operator_checklist_url"]):
        errors.append("override reopen checklist is missing")
    errors.extend(constructor_errors(constructor, current_block=current_block))

    authority = manifest["switchboard_authority"]
    expected_entries = set(EXPECTED_SWITCHBOARDS)
    actual_entries = {
        entry.get("name") for entry in authority["registered_deployment_inventory"]
    }
    if actual_entries != expected_entries:
        errors.append("registered switchboard deployment inventory is incomplete or unknown")
    for entry in authority["registered_deployment_inventory"]:
        expected_fields = {
            "name",
            "address",
            "code_hash",
            "selectors_sha256",
            "reachable_lane_selectors",
            "generic_execution",
        }
        if set(entry) != expected_fields:
            errors.append(f"switchboard inventory fields invalid: {entry.get('name')}")
            continue
        if not ADDRESS_PATTERN.fullmatch(entry.get("address", "")):
            errors.append(f"switchboard address invalid: {entry.get('name')}")
        if not HASH_PATTERN.fullmatch(entry.get("code_hash", "")):
            errors.append(f"switchboard code hash invalid: {entry.get('name')}")
        if not HASH_PATTERN.fullmatch(entry.get("selectors_sha256", "")):
            errors.append(f"switchboard selector hash invalid: {entry.get('name')}")
        if entry.get("reachable_lane_selectors") != EXPECTED_LANE_REACHABILITY.get(
            entry.get("name")
        ):
            errors.append(f"unexpected Lane selector reachability: {entry.get('name')}")
        if entry.get("generic_execution"):
            errors.append(f"generic switchboard execution route: {entry.get('name')}")
    for key in ("inventory_owner", "inventory_block_number"):
        if not _present(authority[key]):
            errors.append(f"switchboard_authority.{key} is missing")
    if authority["unknown_or_generic_routes_found"] is not False:
        errors.append("switchboard selector reachability is not clean")

    fork = manifest["fork_qualification"]
    for key in (
        "archive_rpc_owner",
        "block_number",
        "block_hash",
        "deployment_manifest_sha256",
        "payment_token",
        "payment_decimals",
        "epoch_length",
        "mission_control_topology_sha256",
    ):
        if not _present(fork[key]):
            errors.append(f"fork_qualification.{key} is missing")
    if not fork["approved"] or not fork["unlocked_purchase_passed"] or not fork["locked_purchase_passed"]:
        errors.append("credentialed fork qualification is incomplete")

    indexer = manifest["indexer"]
    if not indexer["event_schema_approved"]:
        errors.append("indexer event schema is not approved")
    for key in ("consumer_owner", "requirements_url"):
        if not _present(indexer[key]):
            errors.append(f"indexer.{key} is missing")
    if not manifest["activation_approved"]:
        errors.append("activation_approved is false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check-draft", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--current-block", type=int, default=0)
    args = parser.parse_args()
    if args.check_draft == args.require_ready:
        parser.error("choose exactly one of --check-draft or --require-ready")

    manifest = load_manifest(args.manifest)
    errors = (
        readiness_errors(manifest, current_block=args.current_block)
        if args.require_ready
        else draft_errors(manifest)
    )
    if errors:
        prefix = "activation blocked" if args.require_ready else "invalid draft"
        print(prefix + ":")
        for error in errors:
            print(f"- {error}")
        return 1
    print("activation manifest is ready" if args.require_ready else "activation draft is valid and blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
