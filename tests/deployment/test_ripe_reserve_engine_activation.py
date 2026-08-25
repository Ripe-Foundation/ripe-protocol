import copy
import json
from pathlib import Path

from scripts.qualify_ripe_reserve_engine_activation import (
    ENGINE_MUTATORS,
    EXPECTED_SWITCHBOARDS,
    constructor_errors,
    draft_errors,
    load_manifest,
    readiness_errors,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "ripe-reserve-engine-activation.json"


def manifest():
    return load_manifest(MANIFEST)


def test_activation_manifest_is_structurally_valid_but_fail_closed():
    data = manifest()
    assert draft_errors(data) == []
    errors = readiness_errors(data, current_block=1)
    assert errors
    assert "activation_approved is false" in errors
    assert "pricing calibration is not approved" in errors
    assert "credentialed fork qualification is incomplete" in errors
    assert "indexer event schema is not approved" in errors


def test_owner_policies_cannot_be_relaxed_in_the_draft():
    mutations = (
        ("runtime_limits", "eip170", 24_577),
        ("design", "allocation_budget_scope", "per_engine"),
        ("design", "claims_replenish_budget", True),
        ("design", "mint_on_claim", False),
        ("design", "dynamic_registry_addresses", False),
        ("design", "cliff_mode", "linear_after_cliff"),
        ("design", "beneficiary_blacklist_enforced", False),
        ("pricing", "snapshot_only_mid_epoch", False),
        ("pricing", "timing_is_strategically_selectable", False),
        ("acquisition_execution", "full_fill_only", False),
        ("rate_override", "mode", "indefinite"),
        ("rate_override", "install_and_cancel_immediate", False),
        ("registry", "vesting_id", 28),
        ("switchboard_authority", "model", "foxtrot_only"),
        ("deployment", "proxy_permitted", True),
    )
    for section, key, value in mutations:
        data = manifest()
        data[section][key] = value
        assert draft_errors(data), (section, key)


def test_switchboard_source_inventory_and_engine_methods_are_pinned():
    data = manifest()
    assert tuple(data["switchboard_authority"]["source_inventory"]) == (
        EXPECTED_SWITCHBOARDS
    )
    assert ENGINE_MUTATORS == (
        "setConfig",
        "setCanAcquireRipe",
        "setRateOverride",
        "cancelRateOverride",
    )
    assert draft_errors(data) == []


def _deployment(**overrides):
    values = {
        "ripe_hq": "0x" + "11" * 20,
        "payment_token": "0x" + "22" * 20,
        "payment_decimals": 6,
        "configured_epoch_length": 1_000,
        "approved_max_epoch_length": 10_000,
        "start_genesis_block": 1_000_100,
        "approved_max_genesis_lead_blocks": 1_000,
        "post_deploy_state_verified": True,
        "deployed_engine": "0x" + "33" * 20,
        "deployed_vesting": "0x" + "44" * 20,
        "deployed_foxtrot": "0x" + "55" * 20,
        "engine_code_hash": "0x" + "66" * 32,
        "vesting_code_hash": "0x" + "77" * 32,
        "foxtrot_code_hash": "0x" + "88" * 32,
        "proxy_permitted": False,
        "proxy_implementation_code_hash": "",
    }
    values.update(overrides)
    if "observed_state" not in overrides:
        values["observed_state"] = {
            "engine_ripe_hq": values["ripe_hq"],
            "engine_payment_token": values["payment_token"],
            "engine_payment_decimals": values["payment_decimals"],
            "engine_payment_scale": 10 ** values["payment_decimals"],
            "vesting_ripe_hq": values["ripe_hq"],
            "registry_engine": values["deployed_engine"],
            "registry_vesting": values["deployed_vesting"],
        }
    return values


def test_named_deployment_plan_rejects_transposition_and_implausible_values():
    assert constructor_errors(_deployment(), current_block=1_000_000) == []
    assert constructor_errors(
        _deployment(
            configured_epoch_length=10_001,
            approved_max_epoch_length=10_000,
        ),
        current_block=1_000_000,
    )
    assert constructor_errors(
        _deployment(start_genesis_block=1_001_001),
        current_block=1_000_000,
    )
    assert constructor_errors(
        _deployment(payment_decimals=74),
        current_block=1_000_000,
    )


def test_start_genesis_zero_and_bounded_values_are_valid():
    current = 1_000_000
    for genesis in (0, current - 1, current, current + 1_000):
        assert constructor_errors(
            _deployment(start_genesis_block=genesis),
            current_block=current,
        ) == []


def test_deployment_state_and_proxy_topology_are_fail_closed():
    current = 1_000_000
    assert constructor_errors(
        _deployment(engine_code_hash=""), current_block=current
    )
    assert constructor_errors(
        _deployment(proxy_permitted=True), current_block=current
    )
    assert constructor_errors(
        _deployment(proxy_implementation_code_hash="0x" + "99" * 32),
        current_block=current,
    )
    mismatched = copy.deepcopy(_deployment()["observed_state"])
    mismatched["registry_vesting"] = "0x" + "aa" * 20
    assert "observed state mismatch: registry_vesting" in constructor_errors(
        _deployment(observed_state=mismatched),
        current_block=current,
    )


def test_unknown_or_generic_registered_switchboard_blocks_readiness():
    data = manifest()
    data["switchboard_authority"]["registered_deployment_inventory"] = [
        {
            "name": name,
            "address": "0x" + f"{index + 1:040x}",
            "code_hash": "0x" + "ab" * 32,
            "selectors_sha256": "0x" + "bc" * 32,
            "reachable_engine_selectors": list(
                ENGINE_MUTATORS if name == "SwitchboardFoxtrot" else ()
            ),
            "generic_execution": name == "SwitchboardCharlie",
        }
        for index, name in enumerate(EXPECTED_SWITCHBOARDS)
    ]
    data["switchboard_authority"]["inventory_owner"] = "security"
    data["switchboard_authority"]["inventory_block_number"] = 1
    data["switchboard_authority"]["unknown_or_generic_routes_found"] = False
    errors = readiness_errors(data, current_block=1)
    assert "generic switchboard execution route: SwitchboardCharlie" in errors

    unknown = copy.deepcopy(data)
    unknown["switchboard_authority"]["registered_deployment_inventory"].append(
        {
            "name": "UnknownSwitchboard",
            "address": "0x" + "99" * 20,
            "code_hash": "0x" + "cd" * 32,
            "selectors_sha256": "0x" + "de" * 32,
            "reachable_engine_selectors": [],
            "generic_execution": False,
        }
    )
    assert "registered switchboard inventory is incomplete or unknown" in (
        readiness_errors(unknown, current_block=1)
    )


def test_manifest_is_canonical_json_with_one_trailing_newline():
    data = manifest()
    expected = (
        json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    ).encode()
    assert MANIFEST.read_bytes() == expected
