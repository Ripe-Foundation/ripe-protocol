import copy
import json
from pathlib import Path

from scripts.qualify_instant_bond_lane_activation import (
    EXPECTED_SWITCHBOARDS,
    constructor_errors,
    draft_errors,
    load_manifest,
    readiness_errors,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "instant-bond-lane-activation.json"


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
        ("lock_bonus", "maximum_bps", 1),
        ("pricing", "snapshot_only_mid_epoch", False),
        ("pricing", "timing_is_strategically_selectable", False),
        ("issuance", "mint_budget_scope", "protocol_wide"),
        ("purchase_execution", "full_fill_only", False),
        ("rate_override", "lifetime", "expires"),
        ("switchboard_authority", "model", "foxtrot_only"),
        ("constructor", "proxy_permitted", True),
    )
    for section, key, value in mutations:
        data = manifest()
        data[section][key] = value
        assert draft_errors(data), (section, key)


def test_switchboard_source_inventory_is_complete_and_has_no_generic_route():
    data = manifest()
    assert tuple(data["switchboard_authority"]["source_inventory"]) == (
        EXPECTED_SWITCHBOARDS
    )
    assert draft_errors(data) == []


def _constructor(**overrides):
    values = {
        "ripe_hq": "0x" + "11" * 20,
        "payment_token": "0x" + "22" * 20,
        "payment_decimals": 6,
        "genesis_block": 1_000_100,
        "epoch_length": 1_000,
        "approved_max_epoch_length": 10_000,
        "approved_max_genesis_lead_blocks": 1_000,
        "post_deploy_immutables_verified": True,
        "deployed_lane": "0x" + "33" * 20,
        "deployed_foxtrot": "0x" + "44" * 20,
        "lane_code_hash": "0x" + "55" * 32,
        "foxtrot_code_hash": "0x" + "66" * 32,
        "proxy_permitted": False,
        "proxy_implementation_code_hash": "",
    }
    values.update(overrides)
    if "observed_immutables" not in overrides:
        values["observed_immutables"] = {
            "lane_ripe_hq": values["ripe_hq"],
            "lane_payment_token": values["payment_token"],
            "lane_genesis_block": values["genesis_block"],
            "lane_epoch_length": values["epoch_length"],
            "lane_payment_decimals": values["payment_decimals"],
            "lane_payment_scale": 10 ** values["payment_decimals"],
            "foxtrot_lane": values["deployed_lane"],
        }
    return values


def test_named_constructor_plan_rejects_transposition_and_implausible_values():
    assert constructor_errors(_constructor(), current_block=1_000_000) == []
    assert constructor_errors(
        _constructor(epoch_length=1_000_100, genesis_block=1_000),
        current_block=1_000_000,
    )
    assert constructor_errors(_constructor(epoch_length=0), current_block=1_000_000)
    assert constructor_errors(
        _constructor(epoch_length=10_000), current_block=1_000_000
    ) == []
    assert constructor_errors(
        _constructor(epoch_length=10_001), current_block=1_000_000
    )
    assert constructor_errors(
        _constructor(genesis_block=1_001_001), current_block=1_000_000
    )


def test_named_constructor_plan_allows_past_current_and_bounded_future_genesis():
    current = 1_000_000
    for genesis in (current - 1, current, current + 1_000):
        assert constructor_errors(
            _constructor(genesis_block=genesis), current_block=current
        ) == []


def test_constructor_code_hash_policy_rejects_unapproved_proxy_topology():
    current = 1_000_000
    assert constructor_errors(
        _constructor(lane_code_hash=""), current_block=current
    )
    assert constructor_errors(
        _constructor(
            proxy_permitted=True,
            proxy_implementation_code_hash="",
        ),
        current_block=current,
    )
    assert constructor_errors(
        _constructor(proxy_implementation_code_hash="0x" + "77" * 32),
        current_block=current,
    )
    mismatched = _constructor()["observed_immutables"]
    mismatched["lane_epoch_length"] += 1
    assert "observed immutable mismatch: lane_epoch_length" in constructor_errors(
        _constructor(observed_immutables=mismatched),
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
            "reachable_lane_selectors": list(
                (
                    "setConfig",
                    "setCanBuyNow",
                    "setRateOverride",
                    "cancelRateOverride",
                )
                if name == "SwitchboardFoxtrot"
                else ()
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
            "reachable_lane_selectors": [],
            "generic_execution": False,
        }
    )
    assert "registered switchboard deployment inventory is incomplete or unknown" in readiness_errors(
        unknown, current_block=1
    )


def test_two_lane_replacement_budget_is_aggregated_fail_closed():
    data = manifest()
    issuance = data["issuance"]
    issuance.update(
        deployment_kind="replacement",
        approved_program_budget=1_000,
        proposed_lane_mint_budget=600,
        aggregate_ledger_owner="treasury-operations",
        aggregate_ledger_sha256="0x" + "aa" * 32,
        prior_lane_issuance=[
            {
                "lane": "0x" + "11" * 20,
                "cumulative_minted": 500,
                "retired_block": 123,
            }
        ],
    )
    assert "replacement Lane would exceed aggregate program budget" in readiness_errors(
        data,
        current_block=1,
    )

    issuance["proposed_lane_mint_budget"] = 500
    errors = readiness_errors(data, current_block=1)
    assert "replacement Lane would exceed aggregate program budget" not in errors


def test_manifest_is_canonical_json_with_one_trailing_newline():
    data = manifest()
    expected = (
        json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    ).encode()
    assert MANIFEST.read_bytes() == expected
