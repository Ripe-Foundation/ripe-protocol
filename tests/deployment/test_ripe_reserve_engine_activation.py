import copy
import json
import sys
from pathlib import Path

import pytest

from scripts.qualify_ripe_reserve_engine_activation import (
    BLOCKED_STATUS,
    ENGINE_CONFIG_FIELDS,
    ENGINE_MUTATORS,
    EXPECTED_ENGINE_REACHABILITY,
    EXPECTED_SWITCHBOARDS,
    EXPECTED_VESTING_REACHABILITY,
    READY_STATUS,
    VESTING_MUTATORS,
    constructor_errors,
    draft_errors,
    load_manifest,
    main,
    readiness_errors,
    selector_inventory_sha256,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "ripe-reserve-engine-activation.json"
CURRENT_BLOCK = 1_000_000
PAYMENT_TOKEN = "0x" + "22" * 20
PAYMENT_TOKEN_CODE_HASH = "0x" + "23" * 32
DEPLOYMENT_MANIFEST_HASH = "0x" + "24" * 32
APPROVED_BUDGET = 10_000_000


def manifest():
    return load_manifest(MANIFEST)


def _engine_config(**overrides):
    values = {
        "paymentCapPerEpoch": 1_000_000,
        "minPaymentAmount": 100,
        "maxAllInPayoutRate": 2_000,
        "seedBasePayoutRate": 1_000,
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "minUpBps": 100,
        "maxUpBps": 500,
        "minDownBps": 100,
        "maxDownBps": 500,
        "decayBps": 50,
        "maxDecayEpochs": 4,
        "maxVestingBonus": 1_000,
        "minVestingLength": 100,
        "maxVestingLength": 1_000,
        "epochLength": 1_000,
    }
    values.update(overrides)
    assert tuple(values) == ENGINE_CONFIG_FIELDS
    return values


def _deployment(**overrides):
    values = {
        "chain_id": 8453,
        "ripe_hq": "0x" + "11" * 20,
        "payment_token": PAYMENT_TOKEN,
        "payment_decimals": 6,
        "payment_token_code_hash": PAYMENT_TOKEN_CODE_HASH,
        "configured_epoch_length": 1_000,
        "approved_max_epoch_length": 10_000,
        "start_genesis_block": 1_000_100,
        "approved_max_genesis_lead_blocks": 1_000,
        "deployment_manifest_sha256": DEPLOYMENT_MANIFEST_HASH,
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
            "engine_config": _engine_config(),
            "vesting_ripe_hq": values["ripe_hq"],
            "vesting_remaining_allocation_budget": APPROVED_BUDGET,
            "registry_engine": values["deployed_engine"],
            "registry_vesting": values["deployed_vesting"],
            "engine_paused": False,
            "vesting_paused": False,
            "ripe_token_paused": False,
            "engine_is_running": True,
            "engine_can_acquire_ripe": True,
            "hq_can_mint_ripe_engine": True,
            "foxtrot_registered_switchboard": True,
        }
    return values


def _switchboard_inventory(deployment):
    entries = []
    for index, name in enumerate(EXPECTED_SWITCHBOARDS):
        engine_selectors = list(EXPECTED_ENGINE_REACHABILITY[name])
        vesting_selectors = list(EXPECTED_VESTING_REACHABILITY[name])
        is_foxtrot = name == "SwitchboardFoxtrot"
        entries.append(
            {
                "name": name,
                "address": deployment["deployed_foxtrot"]
                if is_foxtrot
                else "0x" + f"{index + 1:040x}",
                "code_hash": deployment["foxtrot_code_hash"]
                if is_foxtrot
                else "0x" + f"{index + 1:064x}",
                "selectors_sha256": selector_inventory_sha256(
                    engine_selectors, vesting_selectors
                ),
                "reachable_engine_selectors": engine_selectors,
                "reachable_vesting_selectors": vesting_selectors,
                "generic_execution": False,
            }
        )
    return entries


def _ready_manifest():
    data = manifest()
    data["status"] = READY_STATUS
    data["activation_approved"] = True
    data["pricing"].update(
        {
            "calibration_approved": True,
            "calibration_owner": "economics",
            "calibration_artifact_sha256": "0x" + "91" * 32,
            "approved_min_up_bps": 100,
            "approved_max_up_bps": 500,
            "maximum_acceptable_late_sellout_catch_up_epochs": 4,
            "approved_engine_config": _engine_config(),
        }
    )
    data["allocation"].update(
        {
            "remaining_budget": APPROVED_BUDGET,
            "budget_owner": "treasury",
            "budget_evidence_sha256": "0x" + "92" * 32,
        }
    )
    data["payment_token"].update(
        {
            "chain_id": 8453,
            "address": PAYMENT_TOKEN,
            "decimals": 6,
            "code_hash": PAYMENT_TOKEN_CODE_HASH,
            "qualification_owner": "security",
            "qualification_evidence_url": "https://example.com/payment",
            "monitoring_owner": "operations",
            "pause_authority": "governance",
        }
    )
    data["acquisition_execution"]["client_retry_guidance_url"] = (
        "https://example.com/retry"
    )
    data["rate_override"]["operator_checklist_url"] = (
        "https://example.com/override"
    )
    deployment = _deployment()
    data["deployment"] = deployment
    data["switchboard_authority"].update(
        {
            "registered_deployment_inventory": _switchboard_inventory(deployment),
            "inventory_owner": "security",
            "inventory_block_number": CURRENT_BLOCK,
            "unknown_or_generic_routes_found": False,
        }
    )
    data["fork_qualification"].update(
        {
            "approved": True,
            "archive_rpc_owner": "security",
            "chain_id": 8453,
            "block_number": CURRENT_BLOCK,
            "block_hash": "0x" + "93" * 32,
            "deployment_manifest_sha256": DEPLOYMENT_MANIFEST_HASH,
            "payment_token": PAYMENT_TOKEN,
            "payment_decimals": 6,
            "payment_token_code_hash": PAYMENT_TOKEN_CODE_HASH,
            "epoch_length": 1_000,
            "mission_control_topology_sha256": "0x" + "94" * 32,
            "acquisition_passed": True,
            "direct_claim_passed": True,
            "auto_deposit_claim_passed": True,
        }
    )
    data["indexer"].update(
        {
            "event_schema_approved": True,
            "consumer_owner": "indexing",
            "requirements_url": "https://example.com/indexer",
        }
    )
    return data


def test_activation_manifest_is_structurally_valid_but_fail_closed():
    data = manifest()
    assert data["status"] == BLOCKED_STATUS
    assert draft_errors(data) == []
    errors = readiness_errors(data, current_block=1)
    assert errors
    assert "activation_approved is false" in errors
    assert "pricing calibration is not approved" in errors
    assert "credentialed fork qualification is incomplete" in errors
    assert "indexer event schema is not approved" in errors


def test_complete_synthetic_ready_manifest_passes():
    data = _ready_manifest()
    assert readiness_errors(data, current_block=CURRENT_BLOCK) == []
    assert "draft manifest must not self-authorize activation" in draft_errors(data)


def test_require_ready_cli_accepts_complete_manifest(tmp_path, monkeypatch):
    ready_manifest = tmp_path / "ready.json"
    ready_manifest.write_text(json.dumps(_ready_manifest()))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_ripe_reserve_engine_activation.py",
            "--manifest",
            str(ready_manifest),
            "--require-ready",
            "--current-block",
            str(CURRENT_BLOCK),
        ],
    )
    assert main() == 0


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


@pytest.mark.parametrize(
    ("section", "key"),
    (
        ("pricing", "approved_engine_config"),
        ("deployment", "payment_token_code_hash"),
        ("fork_qualification", "payment_token_code_hash"),
    ),
)
def test_draft_schema_rejects_missing_binding_fields(section, key):
    data = manifest()
    data[section].pop(key)
    assert f"{section} must use the exact named fields" in draft_errors(data)


def test_switchboard_source_inventory_and_mutators_are_pinned():
    data = manifest()
    assert tuple(data["switchboard_authority"]["source_inventory"]) == (
        EXPECTED_SWITCHBOARDS
    )
    assert ENGINE_MUTATORS == (
        "setConfig",
        "setCanAcquireRipe",
        "setRateOverride",
        "cancelRateOverride",
        "start",
        "stop",
        "setPaymentToken",
    )
    assert VESTING_MUTATORS == ("setRemainingAllocationBudget",)
    assert draft_errors(data) == []


def test_named_deployment_plan_rejects_transposition_and_implausible_values():
    assert constructor_errors(_deployment(), current_block=CURRENT_BLOCK) == []
    assert constructor_errors(
        _deployment(
            configured_epoch_length=10_001,
            approved_max_epoch_length=10_000,
        ),
        current_block=CURRENT_BLOCK,
    )
    assert constructor_errors(
        _deployment(start_genesis_block=1_001_001),
        current_block=CURRENT_BLOCK,
    )
    assert constructor_errors(
        _deployment(payment_decimals=74),
        current_block=CURRENT_BLOCK,
    )


def test_start_genesis_zero_and_bounded_values_are_valid():
    for genesis in (0, CURRENT_BLOCK - 1, CURRENT_BLOCK, CURRENT_BLOCK + 1_000):
        assert constructor_errors(
            _deployment(start_genesis_block=genesis),
            current_block=CURRENT_BLOCK,
        ) == []


def test_deployment_state_and_proxy_topology_are_fail_closed():
    assert constructor_errors(
        _deployment(engine_code_hash=""), current_block=CURRENT_BLOCK
    )
    assert constructor_errors(
        _deployment(proxy_permitted=True), current_block=CURRENT_BLOCK
    )
    assert constructor_errors(
        _deployment(proxy_implementation_code_hash="0x" + "99" * 32),
        current_block=CURRENT_BLOCK,
    )
    mismatched = copy.deepcopy(_deployment()["observed_state"])
    mismatched["registry_vesting"] = "0x" + "aa" * 20
    assert "observed state mismatch: registry_vesting" in constructor_errors(
        _deployment(observed_state=mismatched),
        current_block=CURRENT_BLOCK,
    )


@pytest.mark.parametrize(
    ("mutate", "expected_error"),
    (
        (
            lambda data: data["deployment"].__setitem__(
                "payment_token", "0x" + "aa" * 20
            ),
            "payment token address does not match approved deployment",
        ),
        (
            lambda data: data["deployment"].__setitem__("chain_id", 1),
            "payment token chain does not match approved deployment",
        ),
        (
            lambda data: data["deployment"].__setitem__("payment_decimals", 18),
            "payment token decimals does not match approved deployment",
        ),
        (
            lambda data: data["deployment"].__setitem__(
                "payment_token_code_hash", "0x" + "aa" * 32
            ),
            "payment token code hash does not match approved deployment",
        ),
        (
            lambda data: data["deployment"].__setitem__(
                "configured_epoch_length", 999
            ),
            "Engine epoch length does not match approved deployment",
        ),
        (
            lambda data: data["deployment"]["observed_state"][
                "engine_config"
            ].__setitem__("maxUpBps", 501),
            "observed Engine config does not match approved deployment",
        ),
        (
            lambda data: data["deployment"]["observed_state"].__setitem__(
                "vesting_remaining_allocation_budget", APPROVED_BUDGET + 1
            ),
            "observed Vesting budget does not match approved deployment",
        ),
        (
            lambda data: data["deployment"]["observed_state"].__setitem__(
                "engine_can_acquire_ripe", False
            ),
            "observed state mismatch: engine_can_acquire_ripe",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__(
                "payment_token", "0x" + "aa" * 20
            ),
            "fork payment token does not match approved deployment",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__("chain_id", 1),
            "fork chain id does not match approved deployment",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__(
                "payment_decimals", 18
            ),
            "fork payment decimals does not match approved deployment",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__(
                "payment_token_code_hash", "0x" + "aa" * 32
            ),
            "fork payment token code hash does not match approved deployment",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__(
                "deployment_manifest_sha256", "0x" + "aa" * 32
            ),
            "fork deployment manifest does not match approved deployment",
        ),
        (
            lambda data: data["fork_qualification"].__setitem__(
                "epoch_length", 999
            ),
            "fork epoch length does not match approved deployment",
        ),
    ),
)
def test_ready_manifest_cross_bindings_fail_closed(mutate, expected_error):
    data = _ready_manifest()
    mutate(data)
    assert expected_error in readiness_errors(data, current_block=CURRENT_BLOCK)


@pytest.mark.parametrize(
    ("mutate", "expected_error"),
    (
        (
            lambda entry: entry.__setitem__("address", ""),
            "invalid switchboard address: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry.__setitem__("code_hash", "not-a-hash"),
            "invalid switchboard code hash: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry["reachable_engine_selectors"].remove("start"),
            "unexpected Engine selector reachability: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry["reachable_engine_selectors"].append("unknown"),
            "unexpected Engine selector reachability: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry["reachable_vesting_selectors"].clear(),
            "unexpected Vesting selector reachability: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry.__setitem__(
                "selectors_sha256", "0x" + "aa" * 32
            ),
            "invalid switchboard selector hash: SwitchboardFoxtrot",
        ),
        (
            lambda entry: entry.__setitem__("address", "0x" + "aa" * 20),
            "Foxtrot inventory address does not match deployment",
        ),
        (
            lambda entry: entry.__setitem__("code_hash", "0x" + "aa" * 32),
            "Foxtrot inventory code hash does not match deployment",
        ),
    ),
)
def test_switchboard_evidence_values_fail_closed(mutate, expected_error):
    data = _ready_manifest()
    entry = next(
        item
        for item in data["switchboard_authority"][
            "registered_deployment_inventory"
        ]
        if item["name"] == "SwitchboardFoxtrot"
    )
    mutate(entry)
    assert expected_error in readiness_errors(data, current_block=CURRENT_BLOCK)


def test_unknown_or_generic_registered_switchboard_blocks_readiness():
    data = _ready_manifest()
    data["switchboard_authority"]["registered_deployment_inventory"][0][
        "generic_execution"
    ] = True
    errors = readiness_errors(data, current_block=CURRENT_BLOCK)
    assert "generic switchboard execution route: SwitchboardAlpha" in errors

    unknown = _ready_manifest()
    unknown["switchboard_authority"]["registered_deployment_inventory"].append(
        {
            "name": "UnknownSwitchboard",
            "address": "0x" + "99" * 20,
            "code_hash": "0x" + "cd" * 32,
            "selectors_sha256": selector_inventory_sha256([], []),
            "reachable_engine_selectors": [],
            "reachable_vesting_selectors": [],
            "generic_execution": False,
        }
    )
    assert "registered switchboard inventory is incomplete or unknown" in (
        readiness_errors(unknown, current_block=CURRENT_BLOCK)
    )


def test_manifest_is_canonical_json_with_one_trailing_newline():
    data = manifest()
    expected = (
        json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    ).encode()
    assert MANIFEST.read_bytes() == expected
