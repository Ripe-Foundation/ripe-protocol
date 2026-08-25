#!/usr/bin/env python3
"""Fail-closed qualification for Ripe Reserve Engine activation inputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "ripe-reserve-engine-activation.json"
EXPECTED_SWITCHBOARDS = tuple(
    f"Switchboard{name}"
    for name in ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot")
)
ENGINE_MUTATORS = (
    "setConfig",
    "setCanAcquireRipe",
    "setRateOverride",
    "cancelRateOverride",
)
EXPECTED_ENGINE_REACHABILITY = {
    name: list(ENGINE_MUTATORS) if name == "SwitchboardFoxtrot" else []
    for name in EXPECTED_SWITCHBOARDS
}
FOXTROT_SEMANTIC_METHODS = (
    "setReserveEngineConfig",
    "setCanAcquireRipe",
    "setReserveEngineRateOverride",
    "cancelReserveEngineRateOverride",
    "setReserveVestingRemainingAllocationBudget",
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
            "switchboard source inventory changed: "
            f"expected {EXPECTED_SWITCHBOARDS}, got {discovered}"
        )
    configured = tuple(manifest["switchboard_authority"]["source_inventory"])
    if configured != EXPECTED_SWITCHBOARDS:
        errors.append("manifest switchboard source inventory is not canonical")

    for path in paths:
        source = path.read_text()
        if "raw_call(" in source or "method_id(" in source:
            errors.append(
                "generic execution primitive requires review: "
                f"{path.relative_to(root)}"
            )

    foxtrot = (
        root / "contracts" / "config" / "SwitchboardFoxtrot.vy"
    ).read_text()
    for method in FOXTROT_SEMANTIC_METHODS:
        if f"def {method}(" not in foxtrot:
            errors.append(f"Foxtrot semantic method missing: {method}")

    engine = (
        root / "contracts" / "core" / "RipeReserveEngine.vy"
    ).read_text()
    for method in ENGINE_MUTATORS:
        if f"def {method}(" not in engine:
            errors.append(f"Engine mutator missing: {method}")
    return errors


def draft_errors(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors = static_switchboard_errors(root, manifest)
    if manifest.get("schema") != "ripe.reserve-engine.activation.v1":
        errors.append("unexpected activation schema")
    if not manifest.get("owner_decision_url", "").startswith("https://github.com/"):
        errors.append("owner decision evidence URL is missing")
    if manifest.get("runtime_limits") != {"eip170": 24_576}:
        errors.append("runtime limits must be EIP-170 only")

    expected_design = {
        "allocation_budget_scope": "global_remaining_in_vesting",
        "claims_replenish_budget": False,
        "mint_on_claim": True,
        "dynamic_registry_addresses": True,
        "cliff_mode": "catch_up_from_creation",
        "beneficiary_blacklist_enforced": True,
        "vesting_replacement_requires_zero_outstanding_or_migration": True,
    }
    if manifest.get("design") != expected_design:
        errors.append("owner-approved Engine and Vesting design changed")

    pricing = manifest.get("pricing", {})
    if not pricing.get("snapshot_only_mid_epoch"):
        errors.append("mid-epoch pricing must remain snapshot-only")
    if pricing.get("emergency_control") != "pause_or_disable":
        errors.append("emergency control must be pause_or_disable")
    if not pricing.get("timing_is_strategically_selectable"):
        errors.append("strategic timing assumption must be explicit")
    if not manifest.get("acquisition_execution", {}).get("full_fill_only"):
        errors.append("acquisition execution must remain full-fill-only")

    override = manifest.get("rate_override", {})
    expected_override = {
        "mode": "one_shot_named_epoch",
        "install_and_cancel_immediate": True,
        "zero_epoch": "earliest_applicable",
        "invalidated_on_control_or_controller_change": True,
        "ceiling": "maxAllInPayoutRate",
        "operator_checklist_url": override.get("operator_checklist_url", ""),
    }
    if override != expected_override:
        errors.append("owner-approved rate override policy changed")

    registry = manifest.get("registry", {})
    if registry.get("engine_id") != 26 or registry.get("vesting_id") != 27:
        errors.append("RipeHQ registry ids must remain 26 and 27")

    authority = manifest.get("switchboard_authority", {})
    if authority.get("model") != "all_registered_switchboards":
        errors.append("switchboard authority model changed")
    if authority.get("intended_semantic_entrypoint") != "SwitchboardFoxtrot":
        errors.append("Foxtrot semantic entrypoint is not pinned")
    if manifest.get("deployment", {}).get("proxy_permitted"):
        errors.append("proxy deployment is not approved")
    if manifest.get("activation_approved"):
        errors.append("draft manifest must not self-authorize activation")
    return errors


def constructor_errors(
    deployment: dict[str, Any], *, current_block: int
) -> list[str]:
    errors: list[str] = []
    required = {
        "ripe_hq",
        "payment_token",
        "payment_decimals",
        "configured_epoch_length",
        "approved_max_epoch_length",
        "start_genesis_block",
        "approved_max_genesis_lead_blocks",
        "post_deploy_state_verified",
        "observed_state",
        "deployed_engine",
        "deployed_vesting",
        "deployed_foxtrot",
        "engine_code_hash",
        "vesting_code_hash",
        "foxtrot_code_hash",
        "proxy_permitted",
        "proxy_implementation_code_hash",
    }
    if set(deployment) != required:
        return ["deployment configuration must use the exact named fields"]

    address_fields = (
        "ripe_hq",
        "payment_token",
        "deployed_engine",
        "deployed_vesting",
        "deployed_foxtrot",
    )
    for key in address_fields:
        if not ADDRESS_PATTERN.fullmatch(str(deployment[key])):
            errors.append(f"deployment {key} is not an address")

    decimals = deployment["payment_decimals"]
    valid_decimals = isinstance(decimals, int) and 0 <= decimals <= 73
    if not valid_decimals:
        errors.append("deployment payment_decimals is invalid")

    epoch_length = deployment["configured_epoch_length"]
    max_epoch = deployment["approved_max_epoch_length"]
    if not isinstance(epoch_length, int) or epoch_length <= 0:
        errors.append("configured_epoch_length must be positive")
    elif not isinstance(max_epoch, int) or max_epoch <= 0 or epoch_length > max_epoch:
        errors.append("configured_epoch_length exceeds the approved maximum")

    genesis = deployment["start_genesis_block"]
    max_lead = deployment["approved_max_genesis_lead_blocks"]
    if not isinstance(genesis, int) or genesis < 0:
        errors.append("start_genesis_block must be nonnegative")
    elif not isinstance(max_lead, int) or max_lead < 0:
        errors.append("approved genesis lead is invalid")
    elif genesis != 0 and genesis > current_block + max_lead:
        errors.append("start_genesis_block exceeds the approved future lead")

    if not deployment["post_deploy_state_verified"]:
        errors.append("post-deploy state assertions have not passed")

    observed = deployment["observed_state"]
    expected_observed_fields = {
        "engine_ripe_hq",
        "engine_payment_token",
        "engine_payment_decimals",
        "engine_payment_scale",
        "vesting_ripe_hq",
        "registry_engine",
        "registry_vesting",
    }
    if not isinstance(observed, dict) or set(observed) != expected_observed_fields:
        errors.append("observed state must use the exact named fields")
    else:
        expected_values = {
            "engine_ripe_hq": deployment["ripe_hq"],
            "engine_payment_token": deployment["payment_token"],
            "engine_payment_decimals": decimals,
            "engine_payment_scale": 10**decimals if valid_decimals else None,
            "vesting_ripe_hq": deployment["ripe_hq"],
            "registry_engine": deployment["deployed_engine"],
            "registry_vesting": deployment["deployed_vesting"],
        }
        for key, expected in expected_values.items():
            if observed[key] != expected:
                errors.append(f"observed state mismatch: {key}")

    for key in ("engine_code_hash", "vesting_code_hash", "foxtrot_code_hash"):
        if not HASH_PATTERN.fullmatch(str(deployment[key])):
            errors.append(f"deployment {key} is not a code hash")
    if deployment["proxy_permitted"]:
        if not HASH_PATTERN.fullmatch(
            str(deployment["proxy_implementation_code_hash"])
        ):
            errors.append("proxy implementation code hash is missing")
    elif deployment["proxy_implementation_code_hash"]:
        errors.append("proxy implementation hash is set while proxies are forbidden")
    return errors


def readiness_errors(
    manifest: dict[str, Any], *, current_block: int, root: Path = ROOT
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

    allocation = manifest["allocation"]
    for key in ("remaining_budget", "budget_owner", "budget_evidence_sha256"):
        if not _present(allocation[key]):
            errors.append(f"allocation.{key} is missing")
    if _present(allocation["remaining_budget"]) and (
        not isinstance(allocation["remaining_budget"], int)
        or allocation["remaining_budget"] <= 0
    ):
        errors.append("allocation remaining budget is invalid")

    payment = manifest["payment_token"]
    for key in (
        "chain_id",
        "address",
        "decimals",
        "code_hash",
        "qualification_owner",
        "qualification_evidence_url",
        "monitoring_owner",
        "pause_authority",
    ):
        if not _present(payment[key]):
            errors.append(f"payment_token.{key} is missing")
    if payment["callbacks_supported"]:
        errors.append("callback-capable payment tokens are not qualified")
    if _present(payment["address"]) and not ADDRESS_PATTERN.fullmatch(
        payment["address"]
    ):
        errors.append("payment token address is invalid")
    if _present(payment["code_hash"]) and not HASH_PATTERN.fullmatch(
        payment["code_hash"]
    ):
        errors.append("payment token code hash is invalid")

    if not _present(manifest["acquisition_execution"]["client_retry_guidance_url"]):
        errors.append("full-fill retry guidance is missing")
    if not _present(manifest["rate_override"]["operator_checklist_url"]):
        errors.append("override operator checklist is missing")
    errors.extend(
        constructor_errors(manifest["deployment"], current_block=current_block)
    )

    authority = manifest["switchboard_authority"]
    expected_entries = set(EXPECTED_SWITCHBOARDS)
    actual_entries = {
        entry.get("name") for entry in authority["registered_deployment_inventory"]
    }
    if actual_entries != expected_entries:
        errors.append("registered switchboard inventory is incomplete or unknown")
    for entry in authority["registered_deployment_inventory"]:
        expected_fields = {
            "name",
            "address",
            "code_hash",
            "selectors_sha256",
            "reachable_engine_selectors",
            "generic_execution",
        }
        if set(entry) != expected_fields:
            errors.append(f"switchboard inventory fields invalid: {entry.get('name')}")
            continue
        if entry.get("reachable_engine_selectors") != EXPECTED_ENGINE_REACHABILITY.get(
            entry.get("name")
        ):
            errors.append(
                f"unexpected Engine selector reachability: {entry.get('name')}"
            )
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
    required_fork_checks = (
        fork["approved"],
        fork["acquisition_passed"],
        fork["direct_claim_passed"],
        fork["auto_deposit_claim_passed"],
    )
    if not all(required_fork_checks):
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
    print(
        "activation manifest is ready"
        if args.require_ready
        else "activation draft is valid and blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
