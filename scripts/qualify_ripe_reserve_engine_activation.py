#!/usr/bin/env python3
"""Fail-closed qualification for Ripe Reserve Engine activation inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "ripe-reserve-engine-activation.json"
SCHEMA = "ripe.reserve-engine.activation.v2"
BLOCKED_STATUS = "BLOCKED — contract candidate only"
READY_STATUS = "READY — activation approved"
EXPECTED_SWITCHBOARDS = tuple(
    f"Switchboard{name}"
    for name in ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot")
)
ENGINE_MUTATORS = (
    "setConfig",
    "setCanAcquireRipe",
    "setRateOverride",
    "cancelRateOverride",
    "start",
    "stop",
    "setPaymentToken",
)
VESTING_MUTATORS = ("setRemainingAllocationBudget",)
EXPECTED_ENGINE_REACHABILITY = {
    name: list(ENGINE_MUTATORS) if name == "SwitchboardFoxtrot" else []
    for name in EXPECTED_SWITCHBOARDS
}
EXPECTED_VESTING_REACHABILITY = {
    name: list(VESTING_MUTATORS) if name == "SwitchboardFoxtrot" else []
    for name in EXPECTED_SWITCHBOARDS
}
FOXTROT_SEMANTIC_METHODS = (
    "setReserveEngineConfig",
    "setCanAcquireRipe",
    "setReserveEngineRateOverride",
    "cancelReserveEngineRateOverride",
    "startReserveEngine",
    "stopReserveEngine",
    "setReserveEnginePaymentToken",
    "setReserveVestingRemainingAllocationBudget",
    "executePendingAction",
    "cancelPendingAction",
)
ENGINE_CONFIG_FIELDS = (
    "paymentCapPerEpoch",
    "minPaymentAmount",
    "maxAllInPayoutRate",
    "seedBasePayoutRate",
    "uHighBps",
    "uLowBps",
    "minUpBps",
    "maxUpBps",
    "minDownBps",
    "maxDownBps",
    "decayBps",
    "maxDecayEpochs",
    "maxVestingBonus",
    "minVestingLength",
    "maxVestingLength",
    "epochLength",
)
TOP_LEVEL_FIELDS = (
    "schema",
    "status",
    "owner_decision_url",
    "activation_approved",
    "runtime_limits",
    "design",
    "pricing",
    "allocation",
    "payment_token",
    "acquisition_execution",
    "rate_override",
    "registry",
    "deployment",
    "switchboard_authority",
    "fork_qualification",
    "indexer",
)
SECTION_FIELDS = {
    "runtime_limits": ("eip170",),
    "design": (
        "allocation_budget_scope",
        "claims_replenish_budget",
        "mint_on_claim",
        "dynamic_registry_addresses",
        "cliff_mode",
        "beneficiary_blacklist_enforced",
        "vesting_replacement_requires_zero_outstanding_or_migration",
    ),
    "pricing": (
        "snapshot_only_mid_epoch",
        "emergency_control",
        "timing_is_strategically_selectable",
        "calibration_approved",
        "calibration_owner",
        "calibration_artifact_sha256",
        "approved_min_up_bps",
        "approved_max_up_bps",
        "maximum_acceptable_late_sellout_catch_up_epochs",
        "approved_engine_config",
    ),
    "allocation": (
        "remaining_budget",
        "budget_owner",
        "budget_evidence_sha256",
    ),
    "payment_token": (
        "chain_id",
        "address",
        "decimals",
        "code_hash",
        "callbacks_supported",
        "qualification_owner",
        "qualification_evidence_url",
        "monitoring_owner",
        "pause_authority",
    ),
    "acquisition_execution": ("full_fill_only", "client_retry_guidance_url"),
    "rate_override": (
        "mode",
        "install_and_cancel_immediate",
        "zero_epoch",
        "invalidated_on_clock_or_config_change",
        "ceiling",
        "operator_checklist_url",
    ),
    "registry": ("engine_id", "vesting_id"),
    "deployment": (
        "chain_id",
        "ripe_hq",
        "payment_token",
        "payment_decimals",
        "payment_token_code_hash",
        "configured_epoch_length",
        "approved_max_epoch_length",
        "start_genesis_block",
        "approved_max_genesis_lead_blocks",
        "deployment_manifest_sha256",
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
    ),
    "switchboard_authority": (
        "model",
        "intended_semantic_entrypoint",
        "source_inventory",
        "registered_deployment_inventory",
        "inventory_owner",
        "inventory_block_number",
        "unknown_or_generic_routes_found",
    ),
    "fork_qualification": (
        "approved",
        "archive_rpc_owner",
        "chain_id",
        "block_number",
        "block_hash",
        "deployment_manifest_sha256",
        "payment_token",
        "payment_decimals",
        "payment_token_code_hash",
        "epoch_length",
        "mission_control_topology_sha256",
        "acquisition_passed",
        "direct_claim_passed",
        "auto_deposit_claim_passed",
    ),
    "indexer": ("event_schema_approved", "consumer_owner", "requirements_url"),
}
OBSERVED_STATE_FIELDS = (
    "engine_ripe_hq",
    "engine_payment_token",
    "engine_payment_decimals",
    "engine_payment_scale",
    "engine_config",
    "vesting_ripe_hq",
    "vesting_remaining_allocation_budget",
    "registry_engine",
    "registry_vesting",
    "engine_paused",
    "vesting_paused",
    "ripe_token_paused",
    "engine_is_running",
    "engine_can_acquire_ripe",
    "hq_can_mint_ripe_engine",
    "foxtrot_registered_switchboard",
)
EXPECTED_READY_STATE = {
    "engine_paused": False,
    "vesting_paused": False,
    "ripe_token_paused": False,
    "engine_is_running": True,
    "engine_can_acquire_ripe": True,
    "hq_can_mint_ripe_engine": True,
    "foxtrot_registered_switchboard": True,
}
ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH_PATTERN = re.compile(r"^(0x)?[0-9a-fA-F]{64}$")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _valid_address(value: Any) -> bool:
    text = str(value)
    return bool(ADDRESS_PATTERN.fullmatch(text)) and int(text, 16) != 0


def _valid_hash(value: Any) -> bool:
    text = str(value)
    return bool(HASH_PATTERN.fullmatch(text)) and int(text, 16) != 0


def _valid_url(value: Any) -> bool:
    return str(value).startswith(("https://", "http://"))


def selector_inventory_sha256(
    engine_selectors: list[str], vesting_selectors: list[str]
) -> str:
    payload = json.dumps(
        {
            "engine": engine_selectors,
            "vesting": vesting_selectors,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return "0x" + hashlib.sha256(payload).hexdigest()


def manifest_schema_errors(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict) or set(manifest) != set(TOP_LEVEL_FIELDS):
        return ["activation manifest must use the exact top-level fields"]
    errors: list[str] = []
    for section, expected_fields in SECTION_FIELDS.items():
        value = manifest.get(section)
        if not isinstance(value, dict) or set(value) != set(expected_fields):
            errors.append(f"{section} must use the exact named fields")
    pricing = manifest.get("pricing", {})
    approved_config = pricing.get("approved_engine_config")
    if not isinstance(approved_config, dict) or set(approved_config) != set(
        ENGINE_CONFIG_FIELDS
    ):
        errors.append("approved Engine config must use the exact contract fields")
    deployment = manifest.get("deployment", {})
    observed = deployment.get("observed_state")
    if not isinstance(observed, dict) or set(observed) != set(OBSERVED_STATE_FIELDS):
        errors.append("observed state must use the exact named fields")
    return errors


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
    engine_calls = set(
        re.findall(
            r"extcall\s+RipeReserveEngine\([^)]*\)\.([A-Za-z0-9_]+)\(",
            foxtrot,
        )
    )
    if engine_calls != set(ENGINE_MUTATORS):
        errors.append(
            "Foxtrot Engine mutator calls changed: "
            f"expected {sorted(ENGINE_MUTATORS)}, got {sorted(engine_calls)}"
        )
    vesting_calls = set(
        re.findall(
            r"extcall\s+RipeReserveVesting\([^)]*\)\.([A-Za-z0-9_]+)\(",
            foxtrot,
        )
    )
    if vesting_calls != set(VESTING_MUTATORS):
        errors.append(
            "Foxtrot Vesting mutator calls changed: "
            f"expected {sorted(VESTING_MUTATORS)}, got {sorted(vesting_calls)}"
        )

    engine = (
        root / "contracts" / "core" / "RipeReserveEngine.vy"
    ).read_text()
    for method in ENGINE_MUTATORS:
        if f"def {method}(" not in engine:
            errors.append(f"Engine mutator missing: {method}")
    vesting = (
        root / "contracts" / "core" / "RipeReserveVesting.vy"
    ).read_text()
    for method in VESTING_MUTATORS:
        if f"def {method}(" not in vesting:
            errors.append(f"Vesting mutator missing: {method}")
    return errors


def common_errors(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors = manifest_schema_errors(manifest)
    if errors:
        return errors
    errors.extend(static_switchboard_errors(root, manifest))
    if manifest.get("schema") != SCHEMA:
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
        "invalidated_on_clock_or_config_change": True,
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
    return errors


def draft_errors(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors = common_errors(manifest, root)
    if manifest.get("status") != BLOCKED_STATUS:
        errors.append("draft manifest status must remain blocked")
    if manifest.get("activation_approved") is not False:
        errors.append("draft manifest must not self-authorize activation")
    return errors


def constructor_errors(
    deployment: dict[str, Any], *, current_block: int
) -> list[str]:
    errors: list[str] = []
    required = set(SECTION_FIELDS["deployment"])
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
        if not _valid_address(deployment[key]):
            errors.append(f"deployment {key} is not an address")

    chain_id = deployment["chain_id"]
    if not isinstance(chain_id, int) or chain_id <= 0:
        errors.append("deployment chain_id is invalid")

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

    if deployment["post_deploy_state_verified"] is not True:
        errors.append("post-deploy state assertions have not passed")

    observed = deployment["observed_state"]
    expected_observed_fields = set(OBSERVED_STATE_FIELDS)
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
            **EXPECTED_READY_STATE,
        }
        for key, expected in expected_values.items():
            if isinstance(expected, bool):
                mismatched = observed[key] is not expected
            else:
                mismatched = observed[key] != expected
            if mismatched:
                errors.append(f"observed state mismatch: {key}")

    for key in (
        "payment_token_code_hash",
        "deployment_manifest_sha256",
        "engine_code_hash",
        "vesting_code_hash",
        "foxtrot_code_hash",
    ):
        if not _valid_hash(deployment[key]):
            errors.append(f"deployment {key} is not a code hash")
    if deployment["proxy_permitted"]:
        if not _valid_hash(deployment["proxy_implementation_code_hash"]):
            errors.append("proxy implementation code hash is missing")
    elif deployment["proxy_implementation_code_hash"]:
        errors.append("proxy implementation hash is set while proxies are forbidden")
    return errors


def engine_config_errors(config: Any) -> list[str]:
    if not isinstance(config, dict) or set(config) != set(ENGINE_CONFIG_FIELDS):
        return ["approved Engine config must use the exact contract fields"]
    if any(not isinstance(config[key], int) or config[key] < 0 for key in config):
        return ["approved Engine config values must be nonnegative integers"]
    if config["paymentCapPerEpoch"] == 0:
        return ["approved Engine payment cap must be positive"]
    if not 0 < config["minPaymentAmount"] <= config["paymentCapPerEpoch"]:
        return ["approved Engine minimum payment is invalid"]
    if config["epochLength"] == 0:
        return ["approved Engine epoch length must be positive"]
    return []


def readiness_errors(
    manifest: dict[str, Any], *, current_block: int, root: Path = ROOT
) -> list[str]:
    errors = common_errors(manifest, root)
    if manifest.get("status") != READY_STATUS:
        errors.append("ready manifest status is not approved")
    if manifest.get("activation_approved") is not True:
        errors.append("activation_approved is false")

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
    if pricing["calibration_approved"] is not True:
        errors.append("pricing calibration is not approved")
    if _present(pricing["calibration_artifact_sha256"]) and not _valid_hash(
        pricing["calibration_artifact_sha256"]
    ):
        errors.append("pricing calibration artifact hash is invalid")
    approved_config = pricing.get("approved_engine_config")
    errors.extend(engine_config_errors(approved_config))
    if isinstance(approved_config, dict):
        if pricing["approved_min_up_bps"] != approved_config.get("minUpBps"):
            errors.append("approved minimum up bps does not match Engine config")
        if pricing["approved_max_up_bps"] != approved_config.get("maxUpBps"):
            errors.append("approved maximum up bps does not match Engine config")

    allocation = manifest["allocation"]
    for key in ("remaining_budget", "budget_owner", "budget_evidence_sha256"):
        if not _present(allocation[key]):
            errors.append(f"allocation.{key} is missing")
    if _present(allocation["remaining_budget"]) and (
        not isinstance(allocation["remaining_budget"], int)
        or allocation["remaining_budget"] <= 0
    ):
        errors.append("allocation remaining budget is invalid")
    if _present(allocation["budget_evidence_sha256"]) and not _valid_hash(
        allocation["budget_evidence_sha256"]
    ):
        errors.append("allocation budget evidence hash is invalid")

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
    if payment["callbacks_supported"] is not False:
        errors.append("callback-capable payment tokens are not qualified")
    if _present(payment["chain_id"]) and (
        not isinstance(payment["chain_id"], int) or payment["chain_id"] <= 0
    ):
        errors.append("payment token chain id is invalid")
    if _present(payment["decimals"]) and (
        not isinstance(payment["decimals"], int)
        or not 0 <= payment["decimals"] <= 73
    ):
        errors.append("payment token decimals are invalid")
    if _present(payment["address"]) and not _valid_address(payment["address"]):
        errors.append("payment token address is invalid")
    if _present(payment["code_hash"]) and not _valid_hash(payment["code_hash"]):
        errors.append("payment token code hash is invalid")
    if _present(payment["qualification_evidence_url"]) and not _valid_url(
        payment["qualification_evidence_url"]
    ):
        errors.append("payment token qualification evidence URL is invalid")

    retry_url = manifest["acquisition_execution"]["client_retry_guidance_url"]
    if not _present(retry_url):
        errors.append("full-fill retry guidance is missing")
    elif not _valid_url(retry_url):
        errors.append("full-fill retry guidance URL is invalid")
    override_url = manifest["rate_override"]["operator_checklist_url"]
    if not _present(override_url):
        errors.append("override operator checklist is missing")
    elif not _valid_url(override_url):
        errors.append("override operator checklist URL is invalid")

    deployment = manifest["deployment"]
    errors.extend(constructor_errors(deployment, current_block=current_block))
    observed = deployment.get("observed_state", {})
    cross_bindings = (
        ("payment token chain", payment["chain_id"], deployment["chain_id"]),
        ("payment token address", payment["address"], deployment["payment_token"]),
        (
            "payment token decimals",
            payment["decimals"],
            deployment["payment_decimals"],
        ),
        (
            "payment token code hash",
            payment["code_hash"],
            deployment["payment_token_code_hash"],
        ),
        (
            "Engine epoch length",
            approved_config.get("epochLength")
            if isinstance(approved_config, dict)
            else None,
            deployment["configured_epoch_length"],
        ),
        (
            "observed Engine config",
            approved_config,
            observed.get("engine_config"),
        ),
        (
            "observed Vesting budget",
            allocation["remaining_budget"],
            observed.get("vesting_remaining_allocation_budget"),
        ),
    )
    for label, approved, deployed in cross_bindings:
        if approved != deployed:
            errors.append(f"{label} does not match approved deployment")

    authority = manifest["switchboard_authority"]
    expected_entries = set(EXPECTED_SWITCHBOARDS)
    actual_entries = {
        entry.get("name") for entry in authority["registered_deployment_inventory"]
    }
    if (
        actual_entries != expected_entries
        or len(authority["registered_deployment_inventory"])
        != len(EXPECTED_SWITCHBOARDS)
    ):
        errors.append("registered switchboard inventory is incomplete or unknown")
    for entry in authority["registered_deployment_inventory"]:
        expected_fields = {
            "name",
            "address",
            "code_hash",
            "selectors_sha256",
            "reachable_engine_selectors",
            "reachable_vesting_selectors",
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
        if entry.get(
            "reachable_vesting_selectors"
        ) != EXPECTED_VESTING_REACHABILITY.get(entry.get("name")):
            errors.append(
                f"unexpected Vesting selector reachability: {entry.get('name')}"
            )
        if not _valid_address(entry.get("address")):
            errors.append(f"invalid switchboard address: {entry.get('name')}")
        if not _valid_hash(entry.get("code_hash")):
            errors.append(f"invalid switchboard code hash: {entry.get('name')}")
        expected_selector_hash = selector_inventory_sha256(
            entry.get("reachable_engine_selectors", []),
            entry.get("reachable_vesting_selectors", []),
        )
        if entry.get("selectors_sha256") != expected_selector_hash:
            errors.append(f"invalid switchboard selector hash: {entry.get('name')}")
        if entry.get("name") == "SwitchboardFoxtrot":
            if entry.get("address") != deployment["deployed_foxtrot"]:
                errors.append("Foxtrot inventory address does not match deployment")
            if entry.get("code_hash") != deployment["foxtrot_code_hash"]:
                errors.append("Foxtrot inventory code hash does not match deployment")
        if entry.get("generic_execution"):
            errors.append(f"generic switchboard execution route: {entry.get('name')}")
    if not _present(authority["inventory_owner"]):
        errors.append("switchboard_authority.inventory_owner is missing")
    if not isinstance(authority["inventory_block_number"], int) or authority[
        "inventory_block_number"
    ] <= 0:
        errors.append("switchboard authority inventory block is invalid")
    if authority["unknown_or_generic_routes_found"] is not False:
        errors.append("switchboard selector reachability is not clean")

    fork = manifest["fork_qualification"]
    for key in (
        "archive_rpc_owner",
        "chain_id",
        "block_number",
        "block_hash",
        "deployment_manifest_sha256",
        "payment_token",
        "payment_decimals",
        "payment_token_code_hash",
        "epoch_length",
        "mission_control_topology_sha256",
    ):
        if not _present(fork[key]):
            errors.append(f"fork_qualification.{key} is missing")
    if _present(fork["block_hash"]) and not _valid_hash(fork["block_hash"]):
        errors.append("fork block hash is invalid")
    if not isinstance(fork["block_number"], int) or fork["block_number"] <= 0:
        errors.append("fork block number is invalid")
    for key in ("deployment_manifest_sha256", "mission_control_topology_sha256"):
        if _present(fork[key]) and not _valid_hash(fork[key]):
            errors.append(f"fork qualification {key} is invalid")
    if _present(fork["payment_token"]) and not _valid_address(
        fork["payment_token"]
    ):
        errors.append("fork payment token address is invalid")
    if _present(fork["payment_token_code_hash"]) and not _valid_hash(
        fork["payment_token_code_hash"]
    ):
        errors.append("fork payment token code hash is invalid")
    fork_bindings = (
        ("chain id", fork["chain_id"], payment["chain_id"]),
        ("payment token", fork["payment_token"], payment["address"]),
        ("payment decimals", fork["payment_decimals"], payment["decimals"]),
        (
            "payment token code hash",
            fork["payment_token_code_hash"],
            payment["code_hash"],
        ),
        (
            "epoch length",
            fork["epoch_length"],
            deployment["configured_epoch_length"],
        ),
        (
            "deployment manifest",
            fork["deployment_manifest_sha256"],
            deployment["deployment_manifest_sha256"],
        ),
    )
    for label, qualified, approved in fork_bindings:
        if qualified != approved:
            errors.append(f"fork {label} does not match approved deployment")
    required_fork_checks = (
        fork["approved"],
        fork["acquisition_passed"],
        fork["direct_claim_passed"],
        fork["auto_deposit_claim_passed"],
    )
    if not all(value is True for value in required_fork_checks):
        errors.append("credentialed fork qualification is incomplete")

    indexer = manifest["indexer"]
    if indexer["event_schema_approved"] is not True:
        errors.append("indexer event schema is not approved")
    for key in ("consumer_owner", "requirements_url"):
        if not _present(indexer[key]):
            errors.append(f"indexer.{key} is missing")
    if _present(indexer["requirements_url"]) and not _valid_url(
        indexer["requirements_url"]
    ):
        errors.append("indexer requirements URL is invalid")
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
